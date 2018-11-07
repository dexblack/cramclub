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
        self.do_csv_only = ('csv_cache' in self.cram.cfg and
            'only' in self.cram.cfg['csv_cache'] and
            self.cram.cfg['csv_cache']['only'])


    def start_process(self):
        """Check the time to start processing"""
        when = time.strptime(self.cram.cfg['runat'], '%H:%M')
        now = time.localtime()
        start = (now.tm_hour == when.tm_hour and
            now.tm_min == when.tm_min or (
                'instance' in self.cram.cfg and self.cram.cfg['instance'] == 'test'))
        return start


    def stop_process(self):
        """Look for process stop file"""
        return os.path.exists(self.cram.cfg['stop_file_path'])


    def process_group(self, crm, group):
        """
        Pull the contact list for the group from CiviCRM,
        then update corresponding club phonebook.
        """
        self.logger.info(' - { crm: "%s", ch: "%s"' % (group["crm"], group["ch"]))
        crm_contacts = self.crmpull.group(group['crm'])

        if self.stop_process():
            self.logger.info('Stopping: club phonebook not updated: "%s"' % group['ch'])
            return

        self.club.phonebook_update(
            phonebook_id=group['ch'],
            crm_contacts=crm_contacts,
            crm_ch_id_map=self.crm_ch_id_map)


    def process_groups(self):
        """
        Interruptable group processing routine.
        The 'cramclub.instance.stop' file is checked prior to each group.
        """
        start = time.time()
        self.crm_ch_id_map = self.club.contacts()
        end = time.time()
        self.logger.info("Retrieving all club contacts took: %d seconds" % int(end-start))
        if ('csv_cache' in self.cram.cfg and
            'csv_file_path' in self.cram.cfg and
            'create' in self.cram.cfg['csv_cache'] and
            self.cram.cfg['csv_cache']['create']
            ):
            # Write CSV output of the generated crm ch id mapping.
            with open(self.cram.cfg['csv_file_path'], 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile, dialect='excel')
                for ch,crm in self.crm_ch_id_map.items():
                    csv_writer.writerow([ch, crm])
                self.logger.info('Created CSV cache file: "%s"' % self.cram.cfg['csv_file_path'])

        if self.do_csv_only:
            # Stop processing here
            return

        self.logger.info('Groups:')
        for group in self.cram.cfg['groups']:
            if self.stop_process():
                self.logger.info('Stopped before updating phonebook: "%s"' % group['ch'])
                break
            self.process_group(group=group)
