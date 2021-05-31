import os
import supervisely_lib as sly
from distutils.util import strtobool

my_app = sly.AppService()

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ['context.slyProjectId'])


SELECTED_TAGS = os.environ['modal.state.tags']
KEEP_ANNS = bool(strtobool(os.environ['modal.state.keepTags']))
INPUT_PROJECT_NAME = str(os.environ['modal.state.inputProjectName'])

api = sly.Api.from_env()


@my_app.callback("unpack_tags")
@sly.timeit
def unpack_tags(api: sly.Api, task_id, context, state, app_logger):
    src_project = api.project.get_info_by_id(PROJECT_ID)
    if src_project.type != str(sly.ProjectType.IMAGES):
        raise Exception("Project {!r} has type {!r}. App works only with type {!r}"
                        .format(src_project.name, src_project.type, sly.ProjectType.IMAGES))

    src_project_meta_json = api.project.get_meta(src_project.id)
    src_project_meta = sly.ProjectMeta.from_json(src_project_meta_json)

    find_tag = False
    for tag_meta in src_project_meta.tag_metas:
        if tag_meta.value_type == sly.TagValueType.ONEOF_STRING or tag_meta.value_type == sly.TagValueType.ANY_STRING:
            find_tag = True
            continue
    if find_tag is False:
        raise Exception("Project {!r} doesn't have tags with valid values".format(src_project.name))

    dst_project = api.project.create(WORKSPACE_ID, INPUT_PROJECT_NAME, description="Unpacked tags", change_name_if_conflict=True)
    sly.logger.info('Destination project is created.',
                    extra={'project_id': dst_project.id, 'project_name': INPUT_PROJECT_NAME})

    api.project.update_meta(dst_project.id, src_project_meta.to_json())
    dst_project_meta_json = api.project.get_meta(dst_project.id)
    dst_project_meta = sly.ProjectMeta.from_json(dst_project_meta_json)

    for dataset in api.dataset.get_list(src_project.id):
        dst_dataset = api.dataset.create(dst_project.id, dataset.name, change_name_if_conflict=True)
        images = api.image.get_list(dataset.id)
        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]
            image_names = [image_info.name for image_info in batch]

            ann_infos = api.annotation.download_batch(dataset.id, image_ids)
            anns = [sly.Annotation.from_json(ann_info.annotation, src_project_meta) for ann_info in ann_infos]

            unpacked_anns = []
            for ann in anns:
                unpacked_img_tags = sly.TagCollection([])
                unpacked_labels = []
                for img_tag in ann.img_tags:
                    if img_tag.name not in SELECTED_TAGS:
                        continue
                    unpacked_img_tag_meta = sly.TagMeta(f"{img_tag.name}_{img_tag.value}", sly.TagValueType.NONE)
                    unpacked_img_tag = sly.Tag(unpacked_img_tag_meta)
                    unpacked_img_tags = unpacked_img_tags.add(unpacked_img_tag)
                    if unpacked_img_tag_meta not in dst_project_meta.tag_metas:
                        dst_project_meta = dst_project_meta.add_tag_meta(unpacked_img_tag_meta)
                        api.project.update_meta(dst_project.id, dst_project_meta.to_json())

                for label in ann.labels:
                    unpacked_lbl_tags = sly.TagCollection([])
                    for lbl_tag in label.tags:
                        if lbl_tag.name not in SELECTED_TAGS:
                            continue
                        unpacked_lbl_tag_meta = sly.TagMeta(f"{lbl_tag.name}_{lbl_tag.value}", sly.TagValueType.NONE)
                        unpacked_lbl_tag = sly.Tag(unpacked_lbl_tag_meta)
                        unpacked_lbl_tags = unpacked_lbl_tags.add(unpacked_lbl_tag)
                        if KEEP_ANNS:
                            unpacked_lbl_tags = unpacked_lbl_tags.add(lbl_tag)
                        if unpacked_lbl_tag_meta not in dst_project_meta.tag_metas:
                            dst_project_meta = dst_project_meta.add_tag_meta(unpacked_lbl_tag_meta)
                            api.project.update_meta(dst_project.id, dst_project_meta.to_json())

                    unpacked_label = label.clone(tags=unpacked_lbl_tags)
                    unpacked_labels.append(unpacked_label)

                unpacked_ann = ann.clone(labels=unpacked_labels, img_tags=unpacked_img_tags)
                if KEEP_ANNS:
                    unpacked_ann = unpacked_ann.add_tags(ann.img_tags)
                else:
                    unpacked_ann = ann.clone(labels=unpacked_labels, img_tags=unpacked_img_tags)

                unpacked_anns.append(unpacked_ann)

            dst_images = api.image.upload_ids(dst_dataset.id, image_names, image_ids)
            dst_image_ids = [dst_img_info.id for dst_img_info in dst_images]
            api.annotation.upload_anns(dst_image_ids, unpacked_anns)

    api.task.set_output_project(task_id, dst_project.id, dst_project.name)
    my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "TEAM_ID": TEAM_ID,
        "WORKSPACE_ID": WORKSPACE_ID
    })
    my_app.run(initial_events=[{"command": "unpack_tags"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
