import os
import json
import supervisely_lib as sly

my_app = sly.AppService()

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ['modal.state.slyProjectId'])

SELECTED_TAGS = json.loads(os.environ['modal.state.tags'])
KEEP_TAGS = os.environ['modal.state.keepTags']
INPUT_PROJECT_NAME = str(os.environ['modal.state.inputProjectName'])

api = sly.Api.from_env()
global dst_project_meta


def unpack_tags(api, ann_tags, tags_to_unpack, dst_project_id):
    global dst_project_meta
    unpacked_project_tags = []
    for tag in ann_tags:
        if tag.name in tags_to_unpack:
            tag_name = f"{tag.name}_{tag.value}"
            tag_meta = dst_project_meta.tag_metas.get(tag_name)
            if tag_meta is None:
                tag_meta = sly.TagMeta(tag_name, sly.TagValueType.NONE)
                tag = sly.Tag(tag_meta)
                dst_project_meta = dst_project_meta.add_tag_meta(tag_meta)
                api.project.update_meta(dst_project_id, dst_project_meta.to_json())
            else:
                tag = sly.Tag(tag_meta)
            unpacked_project_tags.append(tag)
    return unpacked_project_tags


@my_app.callback("unpack_key_value_tags")
@sly.timeit
def unpack_key_value_tags(api: sly.Api, task_id, context, state, app_logger):
    global dst_project_meta
    src_project = api.project.get_info_by_id(PROJECT_ID)
    src_project_meta_json = api.project.get_meta(src_project.id)
    src_project_meta = sly.ProjectMeta.from_json(src_project_meta_json)

    dst_project = api.project.create(WORKSPACE_ID, INPUT_PROJECT_NAME, description="Unpacked tags", change_name_if_conflict=True)
    sly.logger.info('Destination project is created.',
                    extra={'project_id': dst_project.id, 'project_name': INPUT_PROJECT_NAME})

    api.project.update_meta(dst_project.id, src_project_meta.to_json())
    dst_project_meta = src_project_meta.clone()
    progress = sly.Progress('Unpacking tags for images', src_project.images_count, app_logger)
    for dataset in api.dataset.get_list(src_project.id):
        dst_dataset = api.dataset.create(dst_project.id, dataset.name, change_name_if_conflict=True)
        images = api.image.get_list(dataset.id)
        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]
            image_names = [image_info.name for image_info in batch]
            ann_infos = api.annotation.download_batch(dataset.id, image_ids)
            anns = [sly.Annotation.from_json(ann_info.annotation, dst_project_meta) for ann_info in ann_infos]
            unpacked_anns = []
            for ann in anns:
                image_tags = [tag for tag in ann.img_tags]
                unpacked_image_tags = unpack_tags(api, image_tags, SELECTED_TAGS, dst_project.id)
                if KEEP_TAGS == "keep":
                    unpacked_ann = ann.add_tags(unpacked_image_tags)
                    unpacked_labels = []
                    for label in unpacked_ann.labels:
                        unpacked_label_tags = unpack_tags(api, label.tags, SELECTED_TAGS, dst_project.id)
                        unpacked_label = label.add_tags(unpacked_label_tags)
                        unpacked_labels.append(unpacked_label)
                    unpacked_image_tags = sly.TagCollection(unpacked_ann.img_tags)
                    unpacked_ann = ann.clone(labels=unpacked_labels, img_tags=unpacked_image_tags)
                if KEEP_TAGS == "remove":
                    unpacked_image_tags = sly.TagCollection(unpacked_image_tags)
                    unpacked_labels = []
                    for label in ann.labels:
                        unpacked_label_tags = unpack_tags(api, label.tags, SELECTED_TAGS, dst_project.id)
                        unpacked_label = label.clone(tags=sly.TagCollection(unpacked_label_tags))
                        unpacked_labels.append(unpacked_label)
                    unpacked_ann = ann.clone(labels=unpacked_labels, img_tags=unpacked_image_tags)
                unpacked_anns.append(unpacked_ann)

            dst_images = api.image.upload_ids(dst_dataset.id, image_names, image_ids)
            dst_image_ids = [dst_img_info.id for dst_img_info in dst_images]
            api.annotation.upload_anns(dst_image_ids, unpacked_anns)
            progress.iters_done_report(len(batch))

    api.task.set_output_project(task_id, dst_project.id, dst_project.name)
    my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "TEAM_ID": TEAM_ID,
        "WORKSPACE_ID": WORKSPACE_ID
    })
    my_app.run(initial_events=[{"command": "unpack_key_value_tags"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)