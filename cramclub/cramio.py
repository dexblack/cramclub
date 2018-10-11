"""
Core update code to pull from CiviCRM and push to CallHub.
"""
import os
import time
from cramcfg import CramCfg
from cramlog import CramLog
from cramconst import RETRY_TIME
from crampull import CramPull 


def process_group(group):
    """
    Pull the contact list for the group from CiviCRM,
    then update corresponding CallHub phonebook.
    """
    logger = CramLog.instance()
    logger.info("Group CiviCRM: " + group["crm"] + " CallHub: " + group["ch"])


def process_groups():
    """Use the engine's configuration to control this thread's activity."""
    cram = CramCfg.instance()
    runat = time.strptime(cram.cfg["runat"], "%H:%M")
    while True:
        """Look for process stop file"""
        if os.path.exists(stop_file_path):
            break

        now = time.localtime()
        if now.tm_hour == runat.tm_hour and now.tm_min == runat.tm_min:
            for group in cram.cfg["groups"]:
                process_group(group)

        time.sleep(RETRY_TIME - 1)
