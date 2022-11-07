import supervisely_lib as sly


def unpack_tags(api, ann_tags, tags_to_unpack, dst_project_id, dst_project_meta):
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
    return unpacked_project_tags, dst_project_meta
