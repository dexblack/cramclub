"""
Testing the various Web API behaviour.
"""
from getpass import getpass
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

from cramlog import CramLog
from callhub import CallHub
from crampull import CramPull


def test_getpass():
    passphrase = getpass(prompt='Please type the encryption pass phrase and press Enter:')
    print(passphrase)


def test_secure_config():
    '''
    Pretend the configuration was read from disk.
    The `iv` value is a random string of 32 bytes encoded as bas64.
    '''
    cfg = {
        'instance': 'prod',
        'dir': None,
        'passphrase': None,
        'iv': b64encode(get_random_bytes(32)),
        'callhub': {
            'api_key': '937c82bbb41ce8d7fa898fb57da0dc29c518676b'
        },
        'civicrm': {
            'api_key': 'tPX3X8FqZWJsNZ2Q',
            'site_key': 'c4GmfI7MccoqJFgAFrqPa9y1HnFeKpte'
        },
        'rocket': {'url': 'https://contact-nsw.greens.org.au/agc/ems8#!/contact'},
        'timeout': 20,
        'runat': "03:00",
        'stop_file_path': None
    }
    # pretend the code receives the passphrase from the command line.
    cfg.update({
        'passphrase': 'Some long sentence you remember easily',
        })

    def encipher(cfg, key, subkey):
        '''
        Use AES CBC mode to encrypt the value.
        '''
        result = None
        value = cfg[key][subkey].encode() # UTF-8 byte sequence
        passphrase = cfg['passphrase']
        initial_val = b64decode(cfg['iv'])
        try:
            secure_key = PBKDF2(password=passphrase, salt=initial_val, dkLen=32)
            crypter = AES.new(key=secure_key, mode=AES.MODE_CBC, iv=initial_val[0:16])
            result = crypter.encrypt(value)
        except ValueError as err:
            print(err)
        return result

    def decipher(cfg, key, subkey):
        ''' Decrypt the cfg[key][subkey] value '''
        result = None
        value = b64decode(cfg[key][subkey])
        passphrase = cfg['passphrase']
        initial_val = b64decode(cfg['iv'])
        # Create 32 byte key value for AES-256s
        try:
            secure_key = PBKDF2(password=passphrase, salt=initial_val, dkLen=32)
            crypter = AES.new(key=secure_key, mode=AES.MODE_CBC, iv=initial_val[0:16])
            result = crypter.decrypt(value)
        except ValueError as err:
            print(err)
        return result

    values = [
        ('civicrm', 'api_key'),
        ('civicrm', 'site_key'),
        ('callhub', 'api_key'),
    ]
    for (key, subkey) in values:
        cfg[key][subkey] = b64encode(encipher(cfg, key, subkey))
        print(decipher(cfg, key, subkey))


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
