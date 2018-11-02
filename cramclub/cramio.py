"""
Core update code to pull from CiviCRM and push to CallHub.
"""
import os
import time

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
        self.callhub = CallHub.instance() # pylint: disable-msg=E1101


    def start_process():
        """Check the time to start processing"""
        when = time.strptime(self.cram.cfg['runat'], '%H:%M')
        now = time.localtime()
        start = now.tm_hour == when.tm_hour and (now.tm_min == when.tm_min or True)
        return start


    def stop_process():
        """Look for process stop file"""
        return os.path.exists(self.cram.cfg['stop_file_path'])


    def process_group(crm, group):
        """
        Pull the contact list for the group from CiviCRM,
        then update corresponding CallHub phonebook.
        """
        self.logger.info(' - { crm: "%s", ch: "%s"' % (group["crm"], group["ch"]))
        crm_contacts = self.crmpull.group(group['crm'])

        if self.stop_process():
            self.logger.info('Stopping: CallHub phonebook not updated: "%s"' % group['ch'])
            return

        self.callhub.phonebook_update(
            phonebook_id=group['ch'],
            crm_contacts=crm_contacts,
            crm_ch_id_map=self.crm_ch_id_map)


    def process_groups():
        """Use the engine's configuration to control this thread's activity."""
        start = time.time()
        self.crm_ch_id_map = self.callhub.contacts()
        end = time.time()
        self.logger.info("Retrieving all CallHub contacts took: %d seconds" % int(end-start))

        self.logger.info('Groups:')
        for group in self.cram.cfg['groups']:
            if self.stop_process():
                self.logger.info('Stopped before updating phonebook: "%s"' % group['ch'])
                break
            process_group(group=group)
