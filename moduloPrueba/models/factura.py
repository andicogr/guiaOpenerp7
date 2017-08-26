# coding= utf-8
import logging 

_logger = logging.getLogger(__name__)

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import date, datetime


class factura(osv.osv):

	def tipo_factura(self, cr, uid, context=None):
		return [('venta','Venta'), ('compra','Compra')]


	def _get_nombre_factura(self, cr, uid, ids, name, unknow_none, context=None):
		res = {}
		for record in self.browse(cr, uid, ids, context=context):
			name = ''
			if record.tipo == 'venta':
				name = 'FACTURA DE VENTA'
			elif record.tipo == 'compra':
				name = 'FACTURA DE COMPRA'

			if record.numero:
				name += ' ' + record.numero

			res[record.id] = name
		return res

	_name = 'factura'

	_columns = {
		'name': fields.function(_get_nombre_factura, type="char", string="Nombre"),
		'numero': fields.char('Numero', required=True),
		'tipo': fields.selection(tipo_factura, 'Tipo', required=True),
		'monto_total': fields.integer('Stock', readonly=True),
		'cliente_id': fields.many2one('persona', 'Persona', required=True),
		'fecha_factura': fields.datetime('Fecha de Factura', required=True),
		'comentarios': fields.text('Comentarios'),
		'detalle_ids': fields.one2many('detalle.factura','factura_id', 'Detalle'),
		'detalle_ids2': fields.one2many('detalle.factura2','factura_id', 'Detalle'),
		'state': fields.selection([('borrador','Borrador'),('validada','Validada'),('procesada','Procesada')], 'Estado')
	}

	_defaults = {
		'fecha_factura': str(datetime.now()),
		'state': 'borrador'
	}

	def validar_factura(self, cr, uid, ids, context=None):
		for obj_factura in self.browse(cr, uid, ids):
			monto_total = 0
			for detalle in obj_factura.detalle_ids:
				monto_total += detalle.precio_total
			self.write(cr, uid, [obj_factura.id], {'monto_total': monto_total, 'state': 'validada'})
		return True

	def procesar_factura(self, cr, uid, ids, context=None):
		pool_producto = self.pool['producto']
		for obj_factura in self.browse(cr, uid, ids):
			for detalle in obj_factura.detalle_ids:
				stock_actual = detalle.producto_id.stock
				if obj_factura.tipo == 'venta':
					stock_actual -= detalle.cantidad
				elif obj_factura.tipo == 'compra':
					stock_actual += detalle.cantidad

				pool_producto.write(cr, uid, [detalle.producto_id.id], {'stock': stock_actual})
			self.write(cr, uid, [obj_factura.id], {'state': 'procesada'})
		return True

	def onchange_tipo(self, cr, uid, ids, tipo, context=None):
		if tipo == 'venta':
			return {'domain': {'cliente_id': [('cliente','=',True)]}}
		elif tipo == 'compra':
			return {'domain': {'cliente_id': [('proveedor','=',True)]}}
		return False

	def unlink(self, cr, uid, ids, context=None):

		for factura_id in ids:
			facturaObj = self.browse(cr, uid, factura_id)
			if(facturaObj.state != 'borrador'):
				raise osv.except_osv (_('Error'),
					   _('No puedes eliminar una factura que no se encuentre en estado borrador'))

		return super(factura, self).unlink(cr, uid, ids, context=context)

	def cargar_productos(self, cr, uid, ids, context=None):
		pool_producto = self.pool['producto']
		producto_ids = pool_producto.search(cr, uid, [], order="nombre_producto asc", limit=100)
		lista_productos = []
		for producto in pool_producto.browse(cr, uid, producto_ids):
			lista_productos.append((0,0,{'producto_id': producto.id, 'cantidad': 1, 'precio_unitario': producto.precio, 'precio_total': producto.precio }))

		self.write(cr, uid, ids, {'detalle_ids': lista_productos})
		return True

	def abrir_popup1(self, cr, uid, ids, context=None):
		models_data = self.pool.get('ir.model.data')
		self_obj = self.browse(cr, uid, ids[0])

		dummy, form_view = models_data.get_object_reference(cr, uid, 'moduloPrueba', 'view_wizard_factura_form')
		#dummy, tree_view = models_data.get_object_reference(cr, uid, 'moduloPrueba', 'cip_formalizacion_2008_tree')
		return {
			'name': _('Pop Up'),
			'view_type': 'form',
			'view_mode': 'tree, form',
			'res_model': 'wizard.factura',
			#Id del objeto a donde se queire redireccionar, por ejemplo el id de una factura, y cambiar el res_model por fcatura y el form_view por eld e factura
			'res_id':False,
			'view_id': False,
			'views': [(form_view or False, 'form')],
			'context': {'factura_id': ids[0], 'default_tipo_persona': self_obj.tipo},
			#Con el valor target: new genera un popUp, sin el targe redirecciona a otra ventana
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def redireccionar_cliente(self, cr, uid, ids, context=None):
		self_obj = self.browse(cr, uid, ids[0])
		models_data = self.pool.get('ir.model.data')

		dummy, form_view = models_data.get_object_reference(cr, uid, 'moduloPrueba', 'view_form_modulo_prueba_cliente')
		dummy, tree_view = models_data.get_object_reference(cr, uid, 'moduloPrueba', 'view_tree_modulo_prueba_cliente')
		return {
			'name': _('Cliente'),
			'view_type': 'form',
			'view_mode': 'tree, form',
			'res_model': 'persona',
			'res_id':self_obj.cliente_id.id,
			'view_id': False,
			'views': [(form_view or False, 'form'),(tree_view or False, 'tree')],
			'context': {'factura_id': ids[0] },
			'type': 'ir.actions.act_window',
		}

factura()


class detalle_factura(osv.osv):

	_name = 'detalle.factura'

	_columns = {
		'factura_id': fields.many2one('factura', 'Factura'),
		'producto_id': fields.many2one('producto', 'Producto', required=True),
		'cantidad': fields.integer('Cantidad', required=True),
		'precio_unitario': fields.float('Precio Unitario', required=True),
		'precio_total': fields.float('Precio Total', readonly=True),
	}


detalle_factura()


class detalle_factura2(osv.osv):

	_name = 'detalle.factura2'

	_columns = {
		'factura_id': fields.many2one('factura', 'Factura'),
		'producto_id': fields.many2one('producto', 'Producto', required=True),
		'cantidad': fields.integer('Cantidad', required=True),
		'precio_unitario': fields.float('Precio Unitario', required=True),
		'precio_total': fields.float('Precio Total', readonly=True),
	}

	def onchange_cambiarproducto(self, cr, uid, ids, producto_id, context=None):
		pool_producto = self.pool['producto']
		if not producto_id:
			return {'value': {'precio_unitario': 0, 'cantidad': 0, 'precio_total': 0}}
		producto = pool_producto.browse(cr, uid, producto_id)
		return {'value': {'precio_unitario': producto.precio, 'cantidad': 1, 'precio_total': producto.precio}}

	def onchange_cambiarcantidad(self, cr, uid, ids, precio_unitario, cantidad, context=None):
		_logger.info("precio_unitario %s - cantidad %s", precio_unitario, cantidad)
		if precio_unitario and cantidad:
			return {'value': {'precio_total': precio_unitario * cantidad}}
		else:
			return False

	#Solo se envian los campos que tengan o cambien de valor
	def create(self, cr, uid, values, context=None):
		_logger.info("Values %s", values)

		values['precio_total'] = values['cantidad'] * values['precio_unitario']

		_logger.info("Values %s", values)

		return super(detalle_factura2, self).create(cr, uid, values, context=context)

	#Solo se envian los campos que tengan o cambien de valor, si sabemos que un campo no puede cambiar hay que validar
	def write(self, cr, uid, ids, values, context=None):
		_logger.info("Values %s", values)

		cantidad = values.get('cantidad', False)
		precio_unitario = values.get('precio_unitario', False)

		if not cantidad:
			cantidad = self.browse(cr, uid, ids[0]).cantidad

		if not precio_unitario:
			precio_unitario = self.browse(cr, uid, ids[0]).precio_unitario

		values['precio_total'] =  cantidad * precio_unitario

		_logger.info("Values %s", values)

		return super(detalle_factura2, self).write(cr, uid, ids, values, context=context)


detalle_factura2()