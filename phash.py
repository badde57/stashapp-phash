import os
import sys
import json
import sqlite3

per_page = 10

try:
    import stashapi.log as log
    import stashapi.marker_parse as mp
    from stashapi.stashapp import StashInterface

    import cv2
    from perception import hashers
    hasher = hashers.PHash()

except ModuleNotFoundError:
    print("You need to install the stashapp-tools (stashapi) python module. (CLI: pip install stashapp-tools)", file=sys.stderr)

# plugins don't start in the right directory, let's switch to the local directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

def exit_plugin(msg=None, err=None):
    if msg is None and err is None:
        msg = "plugin ended"
    output_json = {"output": msg, "error": err}
    print(json.dumps(output_json))
    sys.exit()

def catchup():
    log.info('Getting scene count.')
    count=stash.find_scenes(f={},filter={"per_page": 1},get_count=True)[0]
    log.info(str(count)+' scenes to phash.')
    i=0
    for r in range(1,int(count/per_page)+1):
        log.info('fetching data: %s - %s %0.1f%%' % ((r - 1) * per_page,r * per_page,(i/count)*100,))
        scenes=stash.find_scenes(f={},filter={"page":r,"per_page": per_page})
        for s in scenes:
            result = checkphash(s)
            #processScene(s)
            i=i+1
            log.progress((i/count))
            #time.sleep(2)

def checkphash(scene):
    for file in scene['files']:
        scene_id = scene['id']
        path = file['path']
        file_id = file['id']
        fps = float(file['frame_rate'])
        dur = float(file['duration'])
        total_frames = int(dur * fps)
        log.debug(f'processing scene {scene_id}...')

        cur = con.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM phash WHERE file_id = ?",(file_id,))
        rows = cur.fetchall()
        if len(rows) > 0:
            frame_count = int(rows[0][0])
            if frame_count > 100:
                log.debug(f"phash - skipping scene {scene_id}, frame_count={frame_count}")
                continue

        vidcap = cv2.VideoCapture(path)
        success,image = vidcap.read()
        frame = 1
        while success: # and frame < 10
            phash = hasher.compute(image)
            cur.execute('INSERT INTO phash (file_id, frame, phash) VALUES (?,?,?)',(file_id, frame, phash,))
            success,image = vidcap.read()
            frame += 1
            if frame % 1000 == 0:
                log.debug(f'phash - scene: {scene_id}, file: {file_id}, frame: {frame}/{total_frames}, hash: {phash}')
        vidcap.release()
        log.debug(f"phash - finished scene {scene_id}")
        return con.commit()

def main():
    global stash
    json_input = json.loads(sys.stdin.read())
    FRAGMENT_SERVER = json_input["server_connection"]

    #log.debug(FRAGMENT_SERVER)

    stash = StashInterface(FRAGMENT_SERVER)
    PLUGIN_ARGS = False
    HOOKCONTEXT = False

    global con
    phash_db_path = sys.argv[1]
    con = sqlite3.connect(phash_db_path)

    try:
#        PLUGIN_ARGS = json_input['args'].get("mode")
#        PLUGIN_DIR = json_input["PluginDir"]
        PLUGIN_ARGS = json_input['args']["mode"]
    except:
        pass

    if PLUGIN_ARGS:
        log.debug("--Starting Plugin 'phash'--")
        if "catchup" in PLUGIN_ARGS:
            log.info("Catching up with phashing on older files")
            catchup() #loops thru all scenes, and tag
        exit_plugin("phash plugin finished")

    try:
        HOOKCONTEXT = json_input['args']["hookContext"]
    except:
        exit_plugin("phash hook: No hook context")

    log.debug("--Starting Hook 'phash'--")


    sceneID = HOOKCONTEXT['id']
    scene = stash.find_scene(sceneID)

    results = checkphash(scene)
    con.close()
    exit_plugin(results)

main()
