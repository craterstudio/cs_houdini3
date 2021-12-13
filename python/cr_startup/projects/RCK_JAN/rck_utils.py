import os
import sgtk
import json


logger = sgtk.platform.get_logger(__name__)


def get_metadata(hipfile):
    if not os.path.isfile(hipfile):
        raise Exception("File not found: {}".format(hipfile))

    engine = sgtk.platform.current_engine()
    tk = engine.sgtk
    shotgun = engine.sgtk.shotgun

    find = sgtk.util.shotgun.publish_util.find_publish(tk, [hipfile])
    logger.debug(find)

    if not find:
        return None

    if not find.get(hipfile):
        return None

    query = shotgun.find_one(
        "PublishedFile", [["id", "is", find.get(hipfile)["id"]]], ["sg_metadata"])
    logger.debug(query)

    if not query.get("sg_metadata"):
        return None

    metadata = json.loads(query.get("sg_metadata"))
    logger.debug(metadata)

    return metadata
