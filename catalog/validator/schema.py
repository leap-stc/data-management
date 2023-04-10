import pydantic


class Store(pydantic.BaseModel):
    name: str = pydantic.Field(..., description='Name of the store')
    href: pydantic.AnyUrl = pydantic.Field(..., description='URL of the store')


class Link(pydantic.BaseModel):
    label: str = pydantic.Field(..., description='Label of the link')
    href: pydantic.AnyHttpUrl = pydantic.Field(..., description='URL of the link')


class License(pydantic.BaseModel):
    name: str = pydantic.Field(..., description='Name of the license')
    href: pydantic.AnyHttpUrl | None = pydantic.Field(None, description='URL of the license')


class Maintainer(pydantic.BaseModel):
    name: str = pydantic.Field(..., description='Name of the maintainer')
    github_username: str | None = pydantic.Field(
        None, description='GitHub username of the maintainer'
    )


class Dataset(pydantic.BaseModel):
    name: str = pydantic.Field(..., description='Name of the dataset')
    description: str = pydantic.Field(..., description='Description of the dataset')
    stores: list[Store]
    maintainers: list[Maintainer]
    thumbnail: pydantic.HttpUrl | None = pydantic.Field(
        None, description='Thumbnail of the dataset'
    )
    license: License | None = None
    tags: list[str] | None = pydantic.Field(None, description='Tags of the dataset')
    links: list[Link] | None = None
    doi_citation: pydantic.HttpUrl | None = None
    demo: bool = pydantic.Field(False, description='Whether the dataset is a demo dataset')


if __name__ == '__main__':
    import json
    import pathlib

    import yaml

    here = pathlib.Path(__file__).parent

    schema = Dataset.schema()

    # Save the schema to a file
    with open(f'{here}/schema.json', 'w') as f:
        json.dump(schema, f, indent=2)

    # Save the schema to YAML
    with open(f'{here}/schema.yaml', 'w') as f:
        yaml.dump(schema, f)
