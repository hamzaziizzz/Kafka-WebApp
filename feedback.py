import os
import threading
import time
from datetime import datetime

STATUS = None
LAST_UPDATED_STATUS = None
RECOGNIZED_PERSON_LIST = list()
lock = threading.Lock()
STATUS_THRESHOLD = 60


def clear_recognized_person_list():
    """
    This function will reset the global variables
    (STATUS, LAST_STATUS, LAST_UPDATED_STATUS, RECOGNIZED_PERSON_LIST) after every 1 minutes.
    """
    global RECOGNIZED_PERSON_LIST, LAST_UPDATED_STATUS, STATUS, STATUS_THRESHOLD, lock

    while True:
        # Sleep for 1 minutes
        time.sleep(STATUS_THRESHOLD)

        # If the status is updated
        if LAST_UPDATED_STATUS is not None:
            # Checked if the last update time is more than 1 minutes ago
            last_updated_time = datetime.strptime(LAST_UPDATED_STATUS, "%H:%M:%S")
            current_time = datetime.now()
            elapsed_time = current_time - last_updated_time

            if elapsed_time.seconds >= STATUS_THRESHOLD:
                with lock:
                    # Reset the global variables
                    STATUS = None
                    LAST_UPDATED_STATUS = None
                    RECOGNIZED_PERSON_LIST = []


# Create and start the thread to clear the recognized person list
# Set the thread as a daemon, so it will exit when the main program exits
clear_thread = threading.Thread(target=clear_recognized_person_list, daemon=True)
if not clear_thread.is_alive():
    clear_thread.start()


def display_feedback(kafka_message: str):
    """
    This function will display the name of the person recognized and the corresponding camera
    under which the recognition occurred.

    Parameters:
        kafka_message: This is the message to be displayed.
    """
    global STATUS, LAST_UPDATED_STATUS, RECOGNIZED_PERSON_LIST, lock

    # set lock to preserve the integrity of the global variables (STATUS, LAST_STATUS, LAST_UPDATED_STATUS)
    with lock:
        # If no person is recognized
        if STATUS is None:
            STATUS = kafka_message
            LAST_UPDATED_STATUS = datetime.now().strftime("%H:%M:%S")
            person_id, camera_name = kafka_message.split("'")[1], kafka_message.split("'")[3]
            RECOGNIZED_PERSON_LIST.append((person_id, camera_name))
            print(STATUS)
            return STATUS
        # If the person is recognized is different from the last recognized person
        elif STATUS != kafka_message:
            STATUS = kafka_message
            person_id, camera_name = kafka_message.split("'")[1], kafka_message.split("'")[3]
            LAST_UPDATED_STATUS = datetime.now().strftime("%H:%M:%S")
            if (person_id, camera_name) not in RECOGNIZED_PERSON_LIST:
                RECOGNIZED_PERSON_LIST.append((person_id, camera_name))
                print(STATUS)
                return STATUS
