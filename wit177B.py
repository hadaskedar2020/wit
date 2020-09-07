# Upload 177

from datetime import datetime
from distutils.dir_util import copy_tree
import filecmp
import logging
import os
from pathlib import Path
import random
import shutil
import sys

from dateutil import tz

import matplotlib.pyplot as plt
import networkx as nx


STAGING_WIT_PATH = r'.wit\staging_area'
IMAGES_WIT_PATH = r'.wit\images'
REFERENCES_FILE_PATH = r'\.wit\references.txt'


def create_folder(folder_name):
    if os.path.exists(folder_name):
        logging.info(f"Folder '{folder_name}' already exists")
        return
    try:
        os.mkdir(folder_name)
    except OSError as err:
        logging.exception(f"Folder '{folder_name}' creation failed")
        raise err
    else:
        logging.info(f"Folder '{folder_name}' was successfully created")


def write_activated_file(wit_path, text):
    os.chdir(wit_path)
    with open('activated.txt', 'w') as activated_file:
        activated_file.write(text)
    logging.info("File activated.txt was successfully created / updated")


def get_active_branch(wit_path):
    os.chdir(os.path.join(wit_path, '.wit'))
    with open('activated.txt', 'r') as activated_file:
        active_branch = activated_file.read()
    return active_branch


def init():
    create_folder('.wit')
    os.chdir('.wit')
    write_activated_file(os.getcwd(), 'master')
    for folder in ('images', 'staging_area'):
        create_folder(folder)


def basic_full_paths(path):
    if not os.path.exists(path):
        logging.error(f"{path} does not exist. Backup failed.")
        raise OSError(f"{path} does not exist. Backup failed.")
    if os.path.isfile(path):
        parent_dir_full_path = os.path.split(path)[0]
        file_name = os.path.split(path)[1]
        os.chdir(parent_dir_full_path)
        parent_dir_full_path = os.getcwd()
        orig_full_path = os.path.join(parent_dir_full_path, file_name)
    else:
        os.chdir(path)
        orig_full_path = os.getcwd()
        os.chdir('..')
        parent_dir_full_path = os.getcwd()
    return parent_dir_full_path, orig_full_path


def get_wit_path(parent_dir_full_path):
    wit_path = ''
    while os.path.split(parent_dir_full_path)[1] != "" and wit_path == '':
        if os.path.exists(os.path.join(parent_dir_full_path, '.wit')):
            wit_path = parent_dir_full_path
        else:
            parent_dir_full_path = os.path.split(parent_dir_full_path)[0]
    if wit_path == "":
        logging.error(f"There is no directory named: '.wit' on path: {parent_dir_full_path}")
        raise FileNotFoundError(f"There is no directory named: '.wit' on that path: {parent_dir_full_path}.")
    logging.debug(f"wit_path={wit_path}")
    return wit_path


def perform_file_backup(orig_full_path, wit_path):
    logging.debug(f"{len(orig_full_path.split(wit_path))}")
    path_to_generate = orig_full_path.split(wit_path)[1]
    logging.debug(f"perform_file_backup - path_to_generate={path_to_generate}")
    path_to_generate = os.path.split(path_to_generate)[0]
    logging.debug(f"perform_file_backup - path_to_generate={path_to_generate}")
    dst = os.path.join(wit_path, STAGING_WIT_PATH)
    src = orig_full_path
    os.chdir(dst)
    try:
        if len(path_to_generate) > 1:
            os.makedirs(path_to_generate[1:])
    except FileExistsError as err:
        logging.info(f"{err} - Directory already exist - going on with the program")
    try:
        new_file = shutil.copy(src, dst + path_to_generate)
        logging.info(f"File {new_file} has been added to backup")
    except Exception as err:
        logging.exception(f"{err} --> File '{orig_full_path}' backup failed")


def perform_dir_backup(src, dst):
    logging.info(f"perform_dir_backup: {src} - {dst}")
    try:
        new_dir = copy_tree(src, dst)
        logging.info(f"Directory {new_dir} has been added to backup")
    except Exception as err:
        logging.exception(f"{err} --> Directory '{src}' backup failed")


def perform_backup(orig_full_path, wit_path):
    logging.debug(f"perform_backup- orig_full_path={orig_full_path}")
    if not os.path.exists(orig_full_path):
        logging.error(f"{orig_full_path} does not exist. Backup failed.")
        raise OSError(f"{orig_full_path} does not exist. Backup failed.")
    if os.path.isfile(orig_full_path):
        perform_file_backup(orig_full_path, wit_path)
    else:
        path_to_generate = orig_full_path.split(wit_path)[1]
        dst = os.path.join(wit_path, STAGING_WIT_PATH) + path_to_generate
        perform_dir_backup(orig_full_path, dst)


def add(path):
    parent_dir_full_path, orig_full_path = basic_full_paths(path)
    wit_path = get_wit_path(parent_dir_full_path)
    perform_backup(orig_full_path, wit_path)


def create_commit_id_dir(wit_path):
    commit_id_dir_name = ''.join([random.choice('1234567890abcdef') for _ in range(40)])
    if not os.path.exists(os.path.join(wit_path, IMAGES_WIT_PATH)):
        logging.error(f"Folder '{os.path.join(wit_path, IMAGES_WIT_PATH)}' does not exist")
        raise OSError(f"Folder '{os.path.join(wit_path, IMAGES_WIT_PATH)}' does not exist")
    os.chdir(os.path.join(wit_path, IMAGES_WIT_PATH))
    commit_id_dir_path = os.getcwd()
    logging.info(f"Commit id dir: {commit_id_dir_name} has been created at: {commit_id_dir_path}")
    return commit_id_dir_name, commit_id_dir_path


def get_last_commit_id(wit_path, param="HEAD"):
    parent_commit_id = 'None'
    if param:
        try:
            ref_file = open(wit_path + REFERENCES_FILE_PATH, 'r')
        except FileNotFoundError:
            return parent_commit_id
        text = ref_file.read().split('\n')
        ref_file.close()
        for line in text[::-1]:
            if line[:len(param) + 1] == param + '=':
                parent_commit_id = line[len(param) + 1:]
                logging.debug(f"get_last_commit_id - parent_commit_id: {parent_commit_id}")
                return parent_commit_id
    logging.debug(f"get_last_commit_id - parent_commit_id: {parent_commit_id}")
    return parent_commit_id


def create_metadata_file(commit_id_dir_name, commit_id_dir_path, message, wit_path, branch_name=None):
    os.chdir(commit_id_dir_path)
    metadata_file_name = commit_id_dir_name + '.txt'
    with open(metadata_file_name, 'w') as file:
        parent_commit_id = get_last_commit_id(wit_path)
        branch_commit_id = get_last_commit_id(wit_path, branch_name)
        if branch_name != 'None' and parent_commit_id != branch_commit_id:
            parent_commit_id += (',' + branch_commit_id)
        ist_dt = datetime.now(tz=tz.tzlocal())
        display_date_time = ist_dt.strftime("%a %b %d %H:%M:%S %Y %z")
        file.write(f"parent={parent_commit_id}\ndate={display_date_time}\nmessage={message}")
    logging.info(f"Commit id metadata file: {metadata_file_name} has been created at: {commit_id_dir_path}")


def log_to_references(commit_id_dir_name, wit_path):
    last_commit_id_head_number = get_last_commit_id(wit_path, 'HEAD')
    last_commit_id_master_number = get_last_commit_id(wit_path, 'master')
    if last_commit_id_head_number == 'None' or last_commit_id_master_number == 'None':
        with open(wit_path + REFERENCES_FILE_PATH, 'w') as file:
            file.write(f"HEAD={commit_id_dir_name}\nmaster={commit_id_dir_name}\n")
    file = Path(wit_path + '\\' + REFERENCES_FILE_PATH)
    active_branch = get_active_branch(wit_path)
    if last_commit_id_head_number == last_commit_id_master_number and active_branch == 'master':
        file.write_text(file.read_text().replace('HEAD=' + last_commit_id_head_number, 'HEAD=' + commit_id_dir_name))
        file.write_text(file.read_text().replace('master=' + last_commit_id_master_number, 'master=' + commit_id_dir_name))
    else:
        file.write_text(file.read_text().replace('HEAD=' + last_commit_id_head_number, 'HEAD=' + commit_id_dir_name))
    file.write_text(file.read_text().replace(active_branch + '=' + last_commit_id_head_number, active_branch + '=' + commit_id_dir_name))


def commit(message, branch_name=None):
    wit_path = get_wit_path(os.getcwd())
    commit_id_dir_name, commit_id_dir_path = create_commit_id_dir(wit_path)
    create_metadata_file(commit_id_dir_name, commit_id_dir_path, message, wit_path, branch_name)
    perform_dir_backup(os.path.join(wit_path, STAGING_WIT_PATH), os.path.join(commit_id_dir_path, commit_id_dir_name))
    log_to_references(commit_id_dir_name, wit_path)


def get_changed_files(dir_1, dir_2, output_option="both"):
    output = []
    for dirpath, _, filenames in os.walk(dir_1):
        if ".wit" not in dirpath:
            path_to_compare = dir_2 + '\\' + dirpath.split(dir_1)[1]
            for file in filenames:
                if os.path.exists(os.path.join(path_to_compare, file)):
                    if output_option == "both" or output_option == "changed":
                        if not filecmp.cmp(os.path.join(dirpath, file), os.path.join(path_to_compare, file),
                                           shallow=False):
                            output.append(dirpath + '\\' + file)
                else:
                    if output_option == "both" or output_option == "missing":
                        output.append(dirpath + '\\' + file)
    return output


def get_status_info():
    wit_path = get_wit_path(os.getcwd())
    current_commit_id = get_last_commit_id(wit_path)
    stage_dir = os.path.join(wit_path, STAGING_WIT_PATH)
    image_dir = os.path.join(wit_path, IMAGES_WIT_PATH + '\\' + current_commit_id)
    changed_files_stage_image = get_changed_files(stage_dir, image_dir)
    changed_files_stage_origin = get_changed_files(stage_dir, wit_path, "changed")
    changed_files_origin_stage = get_changed_files(wit_path, stage_dir, "missing")
    return current_commit_id, changed_files_stage_image, changed_files_stage_origin, changed_files_origin_stage


def status():
    current_commit_id, changed_files_stage_image, changed_files_stage_origin, changed_files_origin_stage = get_status_info()
    print(f"Current commit id: {current_commit_id}")
    print("Changes to be committed:")
    for file_name in changed_files_stage_image:
        print(file_name)
    print("Changes not staged for commit:")
    for file_name in changed_files_stage_origin:
        print(file_name)
    print("Untracked files:")
    for file_name in changed_files_origin_stage:
        print(file_name)


def update_reference_file(wit_path, commit_id_or_branch_name):
    last_commit = get_last_commit_id(wit_path)
    file = Path(wit_path + '\\' + REFERENCES_FILE_PATH)
    file.write_text(file.read_text().replace('HEAD=' + last_commit, 'HEAD=' + commit_id_or_branch_name))
    commit_id = get_last_commit_id(wit_path, commit_id_or_branch_name + '=')
    if commit_id != 'None':
        write_activated_file(wit_path, commit_id_or_branch_name)


def validate_checkout_input(wit_path, commit_id):
    if commit_id == 'master':
        commit_id = get_last_commit_id(wit_path, 'master')
        logging.debug(commit_id)
    if not os.path.exists(wit_path + '\\' + IMAGES_WIT_PATH + '\\' + commit_id):
        logging.error(f"invalid commit id: {commit_id}")
        raise OSError(f"invalid commit id: {commit_id}")
    return commit_id


def checkout(commit_id_or_branch_name):
    wit_path = get_wit_path(os.getcwd())
    commit_id = get_last_commit_id(wit_path, commit_id_or_branch_name)
    logging.debug(commit_id)
    if commit_id != 'None':
        write_activated_file(wit_path + '\\.wit', commit_id_or_branch_name)
    commit_id = validate_checkout_input(wit_path, commit_id)
    current_commit_id, changed_files_stage_image, changed_files_stage_origin, changed_files_origin_stage = get_status_info()
    if len(changed_files_stage_image) > 0 or len(changed_files_stage_origin) > 0:
        logging.error("Could not complete checkout. There are files that differ between stage-image or origin-stage")
        return
    checkout_path = os.path.join(wit_path, IMAGES_WIT_PATH) + '\\' + commit_id
    perform_dir_backup(checkout_path, wit_path)
    update_reference_file(wit_path, commit_id)


def get_head_number_flow(wit_path, branch_name='HEAD'):
    head_flow = []
    last_commit_id_head_number = get_last_commit_id(wit_path, branch_name)
    head_flow.append(last_commit_id_head_number)
    logging.debug(f"head flow ---> {head_flow}\n")
    path_eclipse = []
    path_eclipse.append(last_commit_id_head_number)
    while path_eclipse:
        path_to_search = os.path.join(wit_path, IMAGES_WIT_PATH) + '\\' + path_eclipse.pop(0) + '.txt'
        if os.path.exists(path_to_search):
            with open(path_to_search, 'r') as file:
                text = file.read().split('\n')
                for parent in text[0].split("parent=")[1].split(','):
                    head_flow.append(parent)
                    path_eclipse.append(parent)
        logging.debug(f"head flow ---> {head_flow}\n path_to_search  ---> {path_to_search} ")
    return head_flow


def get_commits_flow(wit_path, branch_name='HEAD'):
    logging.debug("start of get_commits_flow")
    commits_flow = set()
    commits_to_scan = []
    last_commit_id_number = get_last_commit_id(wit_path, branch_name)
    commits_to_scan.append(last_commit_id_number)
    while commits_to_scan:
        source_commit = commits_to_scan.pop(0)
        path_to_search = os.path.join(wit_path, IMAGES_WIT_PATH) + '\\' + source_commit + '.txt'
        with open(path_to_search, 'r') as file:
            text = file.read().split('\n')
            parents_number = text[0].split("parent=")[1]
            for parent in parents_number.split(','):
                if parent != 'None':
                    commits_flow.add((source_commit, parent))
                    commits_to_scan.append(parent)
    logging.debug(f"commits_flow: {commits_flow}")
    logging.debug("end of get_commits_flow")
    return commits_flow


def draw_flowchart(head_flow, head):
    g = nx.DiGraph()
    g.add_edges_from(head_flow, edge_size=0.1)
    g.add_edge('HEAD', head, label='HEAD', edge_length=0.1, edge_size=0.1)
    edge_colors = ['black' for _ in g.edges()]
    node_colors = ['blue' for _ in range(1, len(g.nodes()) + 1)]
    pos = nx.spring_layout(g)
    nx.draw(g, pos, node_color=node_colors, node_size=500, edge_color=edge_colors, with_labels=True)
    plt.savefig('wit_graph.png')
    plt.show()


def graph():
    wit_path = get_wit_path(os.getcwd())
    commits_flow = get_commits_flow(wit_path)
    head = get_last_commit_id(wit_path)[: 6]
    short_commits_flow = [(flow[0][: 6], flow[1][: 6]) for flow in commits_flow]
    draw_flowchart(short_commits_flow, head)


def add_branch_to_references(branch_name, wit_path):
    last_commit_id_head_number = get_last_commit_id(wit_path, 'HEAD')
    with open(wit_path + REFERENCES_FILE_PATH, 'a') as file:
        file.write(f"{branch_name}={last_commit_id_head_number}\n")


def get_all_branches(wit_path):
    all_branches = []
    try:
        ref_file = open(wit_path + REFERENCES_FILE_PATH, 'r')
    except FileNotFoundError:
        return all_branches
    text = ref_file.read().split('\n')
    ref_file.close()
    for line in text:
        branch = line.split('=')[0]
        if branch != 'HEAD':
            all_branches.append(branch)
    return all_branches


def branch(branch_name):
    wit_path = get_wit_path(os.getcwd())
    all_branches = get_all_branches(wit_path)
    if branch_name not in all_branches:
        add_branch_to_references(branch_name, wit_path)
    else:
        logging.error(f"branch name {branch_name} already exists")
        raise NameError(f"branch name {branch_name} already exists")


def get_common_parent(head_number_flow_commit, head_number_flow_branch):
    for number in head_number_flow_commit:
        if number in head_number_flow_branch:
            logging.debug(f"get_common_parent={number}")
            return number
    return None


def merge(branch_name):
    wit_path = get_wit_path(os.getcwd())
    all_branches = get_all_branches(wit_path)
    if branch_name not in all_branches:
        logging.error(f"branch name {branch_name} does not exist")
        raise NameError(f"branch name {branch_name} does not exist")
    head_number_flow_commit = get_head_number_flow(wit_path)
    head_number_flow_branch = get_head_number_flow(wit_path, branch_name)
    common_parent = get_common_parent(head_number_flow_commit, head_number_flow_branch)
    if not common_parent:
        raise OSError("common parent not found for branch and HEAD")
    commit_path = os.path.join(wit_path, IMAGES_WIT_PATH) + '\\' + common_parent
    logging.debug(f"commit_path={commit_path}")
    changed_files = get_changed_files(wit_path, commit_path, output_option="both")
    logging.debug(changed_files)
    for filepath in changed_files:
        add(filepath)
    commit(f"merge {branch_name}", branch_name)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python <filename> <param1> <param2> [...]")
    else:
        logging.basicConfig(level=logging.DEBUG, filename='logfile.log', format='%(asctime)s --> %(levelname)s: %('
                                                                                'message)s')
        if sys.argv[1] == 'init':
            try:
                init()
            except OSError as err:
                print(f"Could not complete init --> {err}")

        if sys.argv[1] == 'add':
            try:
                add(sys.argv[2])
            except IndexError:
                print("Usage: python <filename> <param1> <param2> [...]")
            except OSError as err:
                print(err)

        if sys.argv[1] == 'commit':
            try:
                commit(sys.argv[2])
            except IndexError:
                print("Usage: python <filename> <param1> <param2> [...]")
            except OSError as err:
                print(err)

        if sys.argv[1] == 'status':
            try:
                status()
            except OSError as err:
                print(err)

        if sys.argv[1] == 'checkout':
            try:
                checkout(sys.argv[2])
            except IndexError:
                print("Usage: python <filename> <param1> <param2> [...]")
            except OSError as err:
                print(err)

        if sys.argv[1] == 'graph':
            try:
                graph()
            except OSError as err:
                print(err)

        if sys.argv[1] == 'branch':
            try:
                branch(sys.argv[2])
            except IndexError:
                print("Usage: python <filename> <param1> <param2> [...]")
            except OSError as err:
                print(err)
            except NameError as err:
                print(err)

        if sys.argv[1] == 'merge':
            try:
                merge(sys.argv[2])
            except IndexError:
                print("Usage: python <filename> <param1> <param2> [...]")
            except OSError as err:
                print(err)
