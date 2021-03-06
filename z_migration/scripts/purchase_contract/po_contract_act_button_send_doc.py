"""
This method will update create_uid follow force_done_reason in purchase order.
"""
import sys
import os
try:
    purchase_path = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.dirname(purchase_path)
    migration_path = os.path.dirname(script_path)
    controller_path = '%s/controller' % migration_path
    sys.path.insert(0, controller_path)
    from connection import connection
    import log
except Exception:
    pass

# Model
PurchaseContract = connection.get_model('purchase.contract')

# Domain
dom = []

# Search PO Contract
poc = PurchaseContract.search_read(dom)

log_po_names = [[], []]
logger = log.setup_custom_logger('po_contract_act_button_send_doc')
logger.info('Start process')
logger.info('Total contract: %s' % len(poc))
for po in poc:
    try:
        ctx = {'bypass_attachment_check': True}
        PurchaseContract.action_button_send_doc([po['id']], context=ctx)
        log_po_names[0].append(po['poc_code'].encode('utf-8'))
        logger.info('Pass: %s' % po['poc_code'])
    except Exception as ex:
        log_po_names[1].append(po['poc_code'].encode('utf-8'))
        logger.error('Fail: %s (reason: %s)' % (po['poc_code'], ex))
summary = 'Summary: pass %s%s and fail %s%s' \
          % (len(log_po_names[0]),
             log_po_names[0] and ' %s' % str(tuple(log_po_names[0])) or '',
             len(log_po_names[1]),
             log_po_names[1] and ' %s' % str(tuple(log_po_names[1])) or '')
logger.info(summary)
logger.info('End process')
