from kgforge.core import KnowledgeGraphForge

import getpass
import json
import pstats
import cProfile

config_path = "./examples/notebooks/use-cases/prod-forge-nexus.yml"

token = getpass.getpass()

forge = KnowledgeGraphForge(
  configuration=config_path,
  endpoint="https://staging.nise.bbp.epfl.ch/nexus/v1",
  bucket="SarahTest/PublicThalamusTest2", token=token
)


entities = forge.search({"type": "Entity"})
print(len(entities))

with cProfile.Profile() as pr:
    test_1 = forge.retrieve([e.id for e in entities])
    pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE).print_stats(10)

with cProfile.Profile() as pr:
    test_2 = [forge.retrieve(e.id) for e in entities]
    pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE).print_stats(10)


assert all(
    json.dumps(forge.as_json(e)) == json.dumps(forge.as_json(e2))
    for e, e2 in zip(test_1, test_2)
)

exit()
