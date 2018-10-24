"""
Core update code to pull from CiviCRM and push to CallHub.
"""
import os
import time
from cramcfg import CramCfg
from cramlog import CramLog
from cramconst import RETRY_TIME
from crampull import CramPull
from callhub import CallHub, missing_crm_contacts



def process_group(crm, club, group, crm_ch_id_map, rocket_url, logger):
    """
    Pull the contact list for the group from CiviCRM,
    then update corresponding CallHub phonebook.
    """
    logger.info(' - { crm: "%s", ch: "%s"' % [ group["crm"], group["ch"] ])
    crm_contacts = crm.group(group["crm"])  # Ahhh symmetry.
    club.phonebook_update(phonebook_id=group["ch"],
                          crm_contacts=crm_contacts,
                          crm_ch_id_map=crm_ch_id_map)


def stop_process(cfg):
    """Look for process stop file"""
    return os.path.exists(cfg["stop_file_path"])


def start_process(cfg):
    """Check the time to start processing"""
    when = time.strptime(cfg["runat"], "%H:%M")
    now = time.localtime()
    start = now.tm_hour == when.tm_hour and (now.tm_min == when.tm_min or True)
    return start


def process_groups():
    """Use the engine's configuration to control this thread's activity."""
    logger = CramLog.instance()
    logger.info("groups:")
    cram = CramCfg.instance()
    crmpull = CramPull.instance()
    club = CallHub.instance()

    while not stop_process(cram.cfg):
        if not start_process(cram.cfg):
            time.sleep(RETRY_TIME)
            continue

        start = time.time()
        crm_ch_id_map = club.contacts()
        end = time.time()
        logger.info("Retrieving CallHub contacts took: %d seconds" % int(end-start))

        for group in cram.cfg["groups"]:
            process_group(crm=crmpull,
                          club=club,
                          group=group,
                          crm_ch_id_map=crm_ch_id_map,
                          rocket_url=cram.cfg["rocket"]["url"],
                          logger=logger)
