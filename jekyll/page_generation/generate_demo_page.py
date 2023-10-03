import jinja2
from google.cloud import storage

def demo_manifest():
    bucket_name = "gibsonchallenge"

    storage_client = storage.Client()

    blobs = storage_client.list_blobs(bucket_name, prefix="behavior_demonstrations/v0.5.0/virtual_reality")

    items = []
    for blob in blobs:
        items.append({
            "url": blob.public_url,
            # If you use prefix, it includes this in the block storage name
            "name": blob.name.split('/')[-1]
        })

    return items

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
template_file = "vr_demos.md.jinja"
template = templateEnv.get_template(template_file)
outputText = template.render(demo_list = demo_manifest())

with open('vr_demos.md', 'w') as f:
    f.write(outputText)
