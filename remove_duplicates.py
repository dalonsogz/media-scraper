import json
import logging

from pymongo import MongoClient

MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_DB = "thegamesdb"
MONGO_COLLECTION = "items"

DUPLICATED_FILE = "duplicated.txt"
DUPLICATED_IDS_FILE = "duplicated_ids.txt"


def findDuplicateGroups(col):
    pipeline = [
        { "$match": { "id": { "$gt": 1 } } },
        { "$group": {
            "_id": { "id": "$id" },
            "count": { "$sum": 1 },
            "docs": { "$push": "$_id" }
        }},
        { "$match": { "count": { "$gt": 1 } } },
        { "$sort": { "_id.id": 1 } }
    ]
    return list(col.aggregate(pipeline))


def writeDuplicatedTxt(results, filename=DUPLICATED_FILE):
    with open(filename, "w", encoding='utf8') as f:
        json.dump(results, f, indent=4, default=str)
        f.write("\n")


def getDuplicatedObjectIds(results):
    objectIds = []
    for result in results:
        docs = result.get("docs") or []
        for doc in docs:
            objectIds.append(doc)
    return objectIds


def writeDuplicatedIdsFile(objectIds, filename=DUPLICATED_IDS_FILE):
    jsLines = [
        "print(",
        "db.getCollection('" + MONGO_COLLECTION + "').remove({",
        '    "_id": {',
        '        "$in": [',
    ]
    lastIndex = len(objectIds) - 1
    for index, objectId in enumerate(objectIds):
        suffix = "," if index < lastIndex else ""
        jsLines.append('            ObjectId("{}"){}'.format(str(objectId), suffix))
    jsLines.append("        ]")
    jsLines.append("    }")
    jsLines.append("})")
    jsLines.append(")")
    with open(filename, "w", encoding='utf8') as f:
        f.write("\n".join(jsLines) + "\n")


def removeDuplicates(col, objectIds):
    if not objectIds:
        return 0
    result = col.delete_many({"_id": {"$in": objectIds}})
    return result.deleted_count


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    col = client[MONGO_DB][MONGO_COLLECTION]
    logging.info("Searching duplicated items in collection {}".format(MONGO_COLLECTION))
    results = findDuplicateGroups(col)
    logging.info("Duplicated item groups found: {}".format(len(results)))
    writeDuplicatedTxt(results)
    objectIds = getDuplicatedObjectIds(results)
    logging.info("Duplicated item ids to remove: {}".format(len(objectIds)))
    writeDuplicatedIdsFile(objectIds)
    deletedCount = removeDuplicates(col, objectIds)
    logging.info("Remove duplicates finished. Deleted documents: {}".format(deletedCount))


if __name__ == "__main__":
    main()
