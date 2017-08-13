# coding= utf-8
import logging 

_logger = logging.getLogger(__name__)

from openerp.osv import fields, osv
from datetime import date

#Documentacion de los tiipos de campos
#https://doc.odoo.com/6.0/developer/2_5_Objects_Fields_Methods/field_type/
#Documentacion de los tipos de atributos de los objetos
#https://doc.odoo.com/6.0/developer/2_5_Objects_Fields_Methods/object_attributes/
class persona(osv.osv):

	def tipo_documento(self, cr, uid, context=None):
		return [('1','DNI'), ('2','RUC')]

	_name = 'persona'

	_columns = {
		'name': fields.char('Nombre'),
		'tipo_documento': fields.selection(tipo_documento, 'Tipo de Documento', required=True),
		'numero_documento': fields.char('Numero Documento', size=11),
		'proveedor': fields.boolean('Proveedor?'),
		'cliente': fields.boolean('Cliente?'),
		'fecha_registro': fields.date('Fecha de Registro', required=True),
		'comentarios': fields.text('Comentarios'),

	}

	_defaults = {
		'fecha_registro': str(date.today()),
		'tipo_documento': '1'
	}

	def _check_length(self, cr, uid, ids, context=None):
		record = self.browse(cr, uid, ids, context=context)
		for persona in record:
			num_doc = persona.numero_documento
			tipo_doc = persona.tipo_documento
			if num_doc and len(num_doc) != 8 and tipo_doc == '1':
				return False
			if num_doc and len(num_doc) != 11 and tipo_doc == '2':
				return False

		return True

	_sql_constraints = [
		('Documento Unico', 'unique(numero_documento)', 'El nummero de documento ya ha sido ingresado!'),
	]

	_constraints = [(_check_length, 'Error: El número de documento no tiene la cantidad de caracteres correctos', ['numero_documento'])]

	def onchange_tipo_documento(self, cr, uid, ids, context=None):
		return {'value': {'numero_documento': ''}}

	def onchange_numero_documento(self, cr, uid, ids, numero_documento, tipo_documento, context=None):
		if numero_documento:
			if tipo_documento == '1' and len(numero_documento) != 8:
				return {'warning': {'tittle': 'Error', 'message': 'El DNI debe tener 8 caracteres'}, 'value': {'numero_documento': False}}
			if tipo_documento == '2' and len(numero_documento) != 11:
				return {'warning': {'tittle': 'Error', 'message': 'El RUC debe tener 11 caracteres'}, 'value': {'numero_documento': False}}
		return {'value': {}}

persona()