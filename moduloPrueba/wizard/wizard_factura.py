# -*- encoding: utf-8 -*-
from osv import osv
from osv import fields
from openerp.tools.translate import _
from datetime import date, datetime
from dateutil import relativedelta
import logging

log = logging.getLogger(__name__)


class wizard_factura(osv.osv_memory):
	_name = 'wizard.factura'
	_description = 'Wizard Factura'
	_columns = {
		'cantidad': fields.integer('Cantidad'),
		'persona_id': fields.many2one('persona', 'Persona'),
		'tipo_persona': fields.char('Tipo Persona (Campo Invisible)'),
	}

	def guardar(self, cr, uid, ids, context=None):
		log.info("Contexto: %s", context)
		wizard_obj = self.browse(cr, uid, ids[0])

		persona_id = wizard_obj.persona_id and wizard_obj.persona_id.id or False
		pool_factura = self.pool['factura']
		pool_producto = self.pool['producto']
		producto_ids = pool_producto.search(cr, uid, [], order="nombre_producto asc", limit=100)
		lista_productos = []
		for producto in pool_producto.browse(cr, uid, producto_ids):
			lista_productos.append((0,0,{'producto_id': producto.id, 'cantidad': wizard_obj.cantidad, 'precio_unitario': producto.precio, 'precio_total': producto.precio * wizard_obj.cantidad }))

		pool_factura.write(cr, uid, context.get('factura_id', context['active_ids']), {'detalle_ids': lista_productos, 'cliente_id': persona_id})


wizard_factura()