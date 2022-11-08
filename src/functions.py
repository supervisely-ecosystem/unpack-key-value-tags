import supervisely as sly


def unpack_tags(api, ann_tags, tags_to_unpack, dst_project_id, dst_project_meta):
    sly.logger.info(msg=f"TAGS TO UNPACK{tags_to_unpack}")
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
            
    sly.logger.info(msg=f"{[tag.name for tag in unpacked_project_tags]}")
    return unpacked_project_tags, dst_project_meta

def remove_original_tags_from_meta(src_project_meta: sly.ProjectMeta, dst_project_meta: sly.ProjectMeta):
    src_tags_names = [tag.name for tag in src_project_meta.tag_metas]
    dst_project_meta = dst_project_meta.delete_tag_metas(tag_names=src_tags_names)
    return dst_project_meta