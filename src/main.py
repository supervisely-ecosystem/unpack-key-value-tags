import supervisely as sly

import functions as f
import globals as g


@g.my_app.callback("unpack_key_value_tags")
@sly.timeit
def unpack_key_value_tags(api: sly.Api, task_id, context, state, app_logger):
    src_project = api.project.get_info_by_id(g.PROJECT_ID)
    src_project_meta_json = api.project.get_meta(src_project.id)
    src_project_meta = sly.ProjectMeta.from_json(src_project_meta_json)

    dst_project = api.project.create(
        g.WORKSPACE_ID,
        g.INPUT_PROJECT_NAME or src_project.name,
        description="Unpacked tags",
        change_name_if_conflict=True,
    )
    sly.logger.info(
        "Destination project is created.",
        extra={"project_id": dst_project.id, "project_name": g.INPUT_PROJECT_NAME},
    )

    api.project.update_meta(dst_project.id, src_project_meta.to_json())
    dst_project_meta = src_project_meta.clone()
    progress = sly.Progress(
        "Unpacking tags for images", src_project.images_count, app_logger
    )
    for dataset in api.dataset.get_list(src_project.id):
        dst_dataset = api.dataset.create(
            dst_project.id, dataset.name, change_name_if_conflict=True
        )
        images = api.image.get_list(dataset.id)
        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]
            image_names = [image_info.name for image_info in batch]
            ann_infos = api.annotation.download_batch(dataset.id, image_ids)
            anns = [
                sly.Annotation.from_json(ann_info.annotation, dst_project_meta)
                for ann_info in ann_infos
            ]
            unpacked_anns = []
            for ann in anns:
                image_tags = list(ann.img_tags)
                unpacked_image_tags, dst_project_meta = f.unpack_tags(
                    api, image_tags, g.SELECTED_TAGS, dst_project.id, dst_project_meta
                )
                if g.KEEP_TAGS == "keep":
                    unpacked_ann = ann.add_tags(unpacked_image_tags)
                    unpacked_labels = []
                    for label in unpacked_ann.labels:
                        unpacked_label_tags, dst_project_meta = f.unpack_tags(
                            api,
                            label.tags,
                            g.SELECTED_TAGS,
                            dst_project.id,
                            dst_project_meta,
                        )
                        unpacked_label = label.add_tags(unpacked_label_tags)
                        unpacked_labels.append(unpacked_label)
                    unpacked_image_tags = sly.TagCollection(unpacked_ann.img_tags)
                    unpacked_ann = ann.clone(
                        labels=unpacked_labels, img_tags=unpacked_image_tags
                    )
                if g.KEEP_TAGS == "remove":
                    unpacked_image_tags = sly.TagCollection(unpacked_image_tags)
                    unpacked_labels = []
                    for label in ann.labels:
                        unpacked_label_tags, dst_project_meta = f.unpack_tags(
                            api,
                            label.tags,
                            g.SELECTED_TAGS,
                            dst_project.id,
                            dst_project_meta,
                        )
                        unpacked_label = label.clone(
                            tags=sly.TagCollection(unpacked_label_tags)
                        )
                        unpacked_labels.append(unpacked_label)
                    unpacked_ann = ann.clone(
                        labels=unpacked_labels, img_tags=unpacked_image_tags
                    )
                unpacked_anns.append(unpacked_ann)

            dst_images = api.image.upload_ids(dst_dataset.id, image_names, image_ids)
            dst_image_ids = [dst_img_info.id for dst_img_info in dst_images]
            api.annotation.upload_anns(dst_image_ids, unpacked_anns)
            progress.iters_done_report(len(batch))

    if g.KEEP_TAGS == "remove":
        dst_project_meta = f.remove_original_tags_from_meta(src_project_meta, dst_project_meta)
        api.project.update_meta(dst_project.id, dst_project_meta.to_json())

    api.task.set_output_project(task_id, dst_project.id, dst_project.name)
    g.my_app.stop()


def main():
    sly.logger.info(
        "Script arguments", extra={"TEAM_ID": g.TEAM_ID, "WORKSPACE_ID": g.WORKSPACE_ID}
    )
    g.my_app.run(initial_events=[{"command": "unpack_key_value_tags"}])

if __name__ == "__main__":
    sly.main_wrapper("main", main)
