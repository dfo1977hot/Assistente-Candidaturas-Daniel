# Input validation policy

External strings are normalized once, bounded and validated before a use case
crosses into Infrastructure. Filenames reject empty/control characters,
absolute/UNC/drive paths, traversal, Windows reserved names, trailing dots or
spaces and unexpected/double extensions. External files have explicit maximum
size plus extension and content/signature validation.

JSON must decode to an object/array within the size limit; CSV and text use
strict UTF-8; XML rejects DTD/entities and is parsed without network access;
ZIP members are inspected for traversal, count, total expansion and suspicious
compression without extraction. Typed safe errors distinguish rejected path,
file, secret, plugin, response, URL and authorization failures.

