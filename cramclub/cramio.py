"""
Core update code to pull from CiviCRM and push to club.
"""
import os
import time
import csv

from cramcfg import CramCfg
from cramlog import CramLog
from crampull import CramPull
from callhub import CallHub



class CramIo(object):
    """
    Core CiviCRM => CallHub processing operations.
    """
    def __init__(self):
        """
        Uses logger, configuration, CiviCRM and CallHub wrappers.
        """
        self.logger = CramLog.instance()  # pylint: disable-msg=E1102
        self.cram = CramCfg.instance()  # pylint: disable-msg=E1102
        self.crmpull = CramPull.instance()  # pylint: disable-msg=E1101
        self.club = CallHub.instance()  # pylint: disable-msg=E1101
        self.crm_ch_id_map = {}


    def start_process(self):
        """Check the time to start processing"""
        when = time.strptime(self.cram.cfg['runat'], '%H:%M')
        now = time.localtime()
        start = (
            now.tm_hour == when.tm_hour and
            now.tm_min == when.tm_min or (
                'instance' in self.cram.cfg and
                self.cram.cfg['instance'] == 'test')
        )
        return start


    def stop_process(self):
        """Look for process stop file"""
        return os.path.exists(self.cram.cfg['stop_file_path'])


    def get_contact_ids_map(self):
        """
        Use the engine's configuration to determine where to gather
        the CallHub <=> CiviCRM id map from.
        """
        has_cache_cfg = 'csv_cache' in self.cram.cfg

        create_cache = has_cache_cfg and \
            'create' in self.cram.cfg['csv_cache'] and \
            self.cram.cfg['csv_cache']['create']

        only_create_cache = create_cache and \
            'only' in self.cram.cfg['csv_cache'] and \
            self.cram.cfg['csv_cache']['only']

        use_cache = has_cache_cfg and \
            'use' in self.cram.cfg['csv_cache'] and \
            self.cram.cfg['csv_cache']['use']

        if create_cache or not use_cache:
            # Retrieve all contacts from CallHub
            # NB: This can take up to an hour for 30000 contacts.
            start = time.time()
            self.crm_ch_id_map = self.club.contacts()
            end = time.time()
            self.logger.info(
                'Retrieving all club contacts took: %d seconds' % int(end-start))

        if create_cache or use_cache:
            csv_file_path = self.cram.cfg['csv_file_path'] \
                if 'csv_file_path' in self.cram.cfg else None

        if create_cache:
            # Write CSV output of the generated crm ch id mapping.
            with open(csv_file_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile, dialect='excel')
                for crm_id, ch_id in self.crm_ch_id_map.items():
                    csv_writer.writerow([crm_id, ch_id])
                self.logger.info('Created CSV cache file: "%s"' % csv_file_path)

        if use_cache:
            # Read CSV output of the generated crm ch id mapping.
            self.logger.info('Using CSV cache file: "%s"' % csv_file_path)
            if not os.path.exists(csv_file_path):
                self.logger.critical('CSV file missing: %s' % csv_file_path)
                return
            with open(csv_file_path, 'r', newline='') as csvfile:
                csv_reader = csv.reader(csvfile, dialect='excel')
                for row in csv_reader:
                    self.crm_ch_id_map[row[0]] = row[1]

        return use_cache or (create_cache and not only_create_cache)


    def process_group(self, crm_group_id, phonebook_id):
        """
        Pull the contact list for the group from CiviCRM,
        then update corresponding CallHub phonebook.
        """
        self.logger.debug('{crm: "%s", ch: "%s"}' % (crm_group_id, phonebook_id))
        crm_contacts = self.crmpull.group(crm_group_id)
        if crm_contacts:
            self.club.phonebook_update(
                phonebook_id=phonebook_id,
                crm_contacts=crm_contacts,
                crm_ch_id_map=self.crm_ch_id_map)
        elif crm_contacts is None:
            # Timed out!
            self.logger.warn('CiviCRM group contacts retrieval timed out. %s' % crm_group_id)
        else:
            self.logger.info('CiviCRM group %s is empty.' % crm_group_id)


    def process_groups(self):
        """Loop through all the configured groups and update them."""
        if not self.get_contact_ids_map():
            return

        self.logger.info('Groups:')
        for group in self.cram.cfg['groups']:
            if self.stop_process():
                self.logger.info(
                    'Stopping: Halted prior to phonebook: "%s"' % group['ch'])
                break
            self.process_group(
                crm_group_id=group['crm'], phonebook_id=group['ch'])
