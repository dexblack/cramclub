from cramlog import CramLog
from callhub import CallHub
from crampull import CramPull


def test_add_contact_to_callhub():
    """
    Checking what happens when we create the same contact twice.
    Do we get the same CallHub contact id back?
    Is it then the equivalent of an update operation?
    """
    logger = CramLog.instance()
    crampull = CramPull.instance()
    club = CallHub.instance()

    crm_id = '213824' # TR
    crm_contact = crampull.contact(crm_id)
    if not crm_contact:
        logger.error('Failed to retrieve CRM contact: ' + crm_id)
        return

    ch_contact = club.make_callhub_contact_from(crm_contact)

    #callhub_contact_fields = club.get_contact_fields()

    result1 = club.create_contact(ch_contact)

    ch_id = '24654185' # TR
    if 'exists' in result1 and result1['exists']:
        logger.debug('Existing contact returned')

    ch_contact2 = {
        'contact': result1['contact']['contact'],
        'last_name': 'Raue_'
        #'job_title': crm_id + '?',
        #'custom_fields': "{u'2170': u'Grayndler', u'2171': u'NSW - Summer Hill', u'2184': u'213824'}"
    }
    result2 = club.update_contact(result1['contact']['id'], ch_contact2)
