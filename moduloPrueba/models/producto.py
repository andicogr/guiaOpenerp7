# coding= utf-8
import logging 

_logger = logging.getLogger(__name__)

from openerp.osv import fields, osv
from datetime import date

class categoria_producto(osv.osv):

	_name = 'categoria.producto'

	_columns = {
		'name': fields.char('Nombre'),
		'activo': fields.boolean('Activo'),
		'descripcion': fields.text('Descripcion'),

	}

	_sql_constraints = [
		('Categoria Unica', 'unique(name)', 'El nombre de la categoria ya ha sido ingresado!'),
	]

categoria_producto()


class producto(osv.osv):

	def tipo_producto(self, cr, uid, context=None):
		return [('producto','Producto'), ('servicio','Servicio')]

	def _obtener_stock_real(self, cr, uid, ids, field_name, arg, context):
		pool_detalle_factura = self.pool['detalle.factura']
		res = {}

		for record in self.browse(cr, uid, ids, context=context):
			sql= """
			SELECT 
				sum(d.cantidad) AS stock_ingreso
			FROM 
				detalle_factura d, factura f
			WHERE 
				f.id = d.factura_id
				AND f.tipo = 'compra'
				AND d.producto_id = %d
			""" % (record.id,)

			cr.execute(sql)
			resultado = cr.dictfetchone()

			stock_ingreso = resultado['stock_ingreso'] or 0

			stock_salida = 0.0
			detalle_ids = pool_detalle_factura.search(cr, uid, [('factura_id.tipo','=','venta'),('producto_id','=',record.id)])
			for detalle in pool_detalle_factura.browse(cr, uid, detalle_ids):
				stock_salida += detalle['cantidad']

			res[record.id] = stock_ingreso - stock_salida
		return res

	_name = 'producto'

	_rec_name = 'nombre_producto'

	_columns = {
		'nombre_producto': fields.char('Nombre', required=True),
		'tipo': fields.selection(tipo_producto, 'Tipo', required=True),
		'stock': fields.integer('Stock', readonly=True),
		'stock_real': fields.function(_obtener_stock_real, type='float', string='Stock Real', readonly=True),
		'precio': fields.float('Precio', required=True),
		'categoria_id': fields.many2one('categoria.producto', 'Categoria', required=True, domain="[('activo','=','True')]"),
		'fecha_registro': fields.date('Fecha de Registro', required=True),
		'descripcion': fields.text('Descripcion'),
	}

	_defaults = {
		'fecha_registro': str(date.today()),
		'stock': 0,
		'precio': 0.00
	}

	def unlink(self, cr, uid, ids, context=None):
		for producto in self.browse(cr, uid, ids):
			if producto.stock != 0:
				raise osv.except_osv(('Error!'),('No se puede eliminar un producto con stock diferente a cero'))
		return super(producto, self).unlink(cr, uid, ids, context=context)

	#Funcionamineto de condiciones
	#[A,B] = A and B
	#[A,B,C] = A and B and C
	#['|',A,B] = A or B
	#['|','&',A,B,C] = A or B and C
	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		args2 = []
		i = 0
		for x in args:
			if not x[0] in ['estado']:
				args2.append(x)
		args = args2
		if not context:
			context = {}
		if name:
			ids = self.search(cr, uid, ['|','|',('nombre_producto', operator, name),('categoria_id.name', '=', name)] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, uid, args, limit=limit, context=context)
		return self.name_get(cr, uid, ids, context)

	def name_get(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		if isinstance(ids, (int, long)):
			ids = [ids]
		reads = self.read(cr, uid, ids, ['nombre_producto', 'stock_real', 'precio'], context=context)
		res = []
		for record in reads:
			_logger.info("Record: %s", record)
			name = 'Producto: '
			if record['nombre_producto']:
				name = record['nombre_producto']
			if record['stock_real']:
				name = name + ' / Stock: ' + str(record['stock_real'])
			if record['precio']:
				name = name + ' / Precio: ' + str(record['precio'])
			res.append((record['id'], name))
		return res

producto()