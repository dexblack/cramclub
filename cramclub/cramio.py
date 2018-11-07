"""
Core update code to pull from CiviCRM and push to club.
"""
import os
import time
import csv

from cramcfg import CramCfg
from cramlog import CramLog
from cramconst import RETRY_TIME
from crampull import CramPull
from callhub import CallHub


class CramIo(object):
    def __init__(self):
        self.logger = CramLog.instance() # pylint: disable-msg=E1102
        self.cram = CramCfg.instance() # pylint: disable-msg=E1102
        self.crmpull = CramPull.instance() # pylint: disable-msg=E1101
        self.club = CallHub.instance() # pylint: disable-msg=E1101
        self.do_csv_only = self.cram.get(False, 'csv_cache', 'only')
        self.use_csv_cache = self.cram.get(False, 'csv_cache', 'use')
        self.csv_file_path = self.cram.cfg['csv_file_path']


    def start_process(self):
        """Check the time to start processing"""
        when = time.strptime(self.cram.cfg['runat'], '%H:%M')
        now = time.localtime()
        start = (now.tm_hour == when.tm_hour and now.tm_min == when.tm_min or (
            'instance' in self.cram.cfg and self.cram.cfg['instance'] == 'test'))
        return start


    def stop_process(self):
        """Look for process stop file"""
        return os.path.exists(self.cram.cfg['stop_file_path'])


    def write_csv(self):
        # Write CSV output of the generated crm ch id mapping.
        with open(self.csv_file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, dialect='excel')
            for ch,crm in self.crm_ch_id_map.items():
                csv_writer.writerow([ch, crm])
            self.logger.info('Created CSV cache file: "%s"' % self.csv_file_path)


    def read_csv(self):
        self.logger.info('Using CSV cache file: "%s"' % self.csv_file_path)
        self.crm_ch_id_map = {}
        with open(self.csv_file_path, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile, dialect='excel')
            for row in csv_reader:
                self.crm_ch_id_map[row[0]] = row[1]


    def phonebook_update(self, group_link):
        """
        Pull the contact list for the group from CiviCRM,
        then update corresponding club phonebook.
        """
        self.logger.info(' - { crm: "%s", ch: "%s"' % (group_link['crm'], group_link['ch']))
        crm_contacts = self.crmpull.group(group_link['crm'])

        if self.stop_process():
            self.logger.info('Stopping: club phonebook not updated: "%s"' % group_link['ch'])
            return

        if crm_contacts:
            self.club.phonebook_update(
                phonebook_id=group_link['ch'],
                crm_contacts=crm_contacts,
                crm_ch_id_map=self.crm_ch_id_map)


    def process_groups(self):
        """
        Interruptable group processing routine.
        The 'cramclub.instance.stop' file is checked prior to each group.
        """
        if self.cram.get(False, 'csv_cache', 'use'):
            self.read_csv()
        else:
            start = time.time()
            self.crm_ch_id_map = self.club.contacts()
            end = time.time()
            self.logger.info("Retrieving all club contacts took: %d seconds" % int(end-start))

            if self.cram.get(False, 'csv_cache', 'create'):
                self.write_csv()

            if self.do_csv_only:
                # Stop processing here
                self.logger.info('CRM Group to CallHub phonebook map CSV cache created.')
                return

        if not self.crm_ch_id_map:
            self.logger.error('CRM Group to CallHub phonebook map is empty!')
            return

        self.logger.info('Groups:')
        for group_link in self.cram.cfg['groups']:
            if self.stop_process():
                self.logger.info('Stopped before updating phonebook: "%s"' % group_link['ch'])
                break
            self.phonebook_update(group_link)
