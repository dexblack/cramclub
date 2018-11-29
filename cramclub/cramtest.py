"""
Testing the various Web API behaviour.
"""
from cramlog import CramLog
from callhub import CallHub
from crampull import CramPull
from cramcrypt import CramCrypt


def test_crypto():
    """ Verify CramCrypt works as expected """
    input = 'c4GmfI7MccoqJFgAFrqPa9y1HnFeKpte'
    iv = b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'
    salt = b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'
    crypter = CramCrypt(iv, salt)
    encrypted = crypter.encrypt(input)
    decrypted = crypter.decrypt(encrypted)
    assert decrypted == input


def test_add_contact_to_callhub():
    """
    Checking what happens when we create the same contact twice.
    Do we get the same CallHub contact id back?
    Is it then the equivalent of an update operation?
    """
    logger = CramLog.instance() # pylint: disable-msg=E1102
    crampull = CramPull.instance() # pylint: disable-msg=E1101
    club = CallHub.instance() # pylint: disable-msg=E1101

    crm_id = '325619' # me
    crm_contact = crampull.contact(crm_id)
    if not crm_contact:
        logger.error('Failed to retrieve CRM contact: ' + crm_id)
        return

    ch_contact = club.make_callhub_contact_from(crm_contact)

    #callhub_contact_fields = club.get_contact_fields()

    result1 = club.create_contact(ch_contact)
    if not result1:
        return

    ch_id = '1910874392879957535' # me
    if not ('exists' in result1 and result1['exists']):
        logger.debug('test_add_contact_to_callhub(): Unexpected error')
        return

    logger.debug('Existing contact returned')

    ch_contact1 = result1['contact']
    if ch_id != ch_contact1['pk_str']:
        return

    result2 = club.update_contact(ch_contact1['pk_str'], ch_contact)
    if result2:
        logger.debug('test_add_contact_to_callhub() updated contact')
