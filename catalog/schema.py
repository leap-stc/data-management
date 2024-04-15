import pydantic
import upath
import yaml


class Store(pydantic.BaseModel):
    id: str = pydantic.Field(..., description='ID of the store')
    name: str = pydantic.Field(None, description='Name of the store')
    url: str = pydantic.Field(..., description='URL of the store')
    rechunking: list[dict[str, str]] | None = pydantic.Field(None, alias='ncviewjs:rechunking')


class Link(pydantic.BaseModel):
    label: str = pydantic.Field(..., description='Label of the link')
    url: str = pydantic.Field(..., description='URL of the link')


class LicenseLink(pydantic.BaseModel):
    title: str = pydantic.Field(..., description='Name of the license')
    url: str | None = pydantic.Field(None, description='URL of the license')


class Maintainer(pydantic.BaseModel):
    name: str = pydantic.Field(..., description='Name of the maintainer')
    github: str | None = pydantic.Field(None, description='GitHub username of the maintainer')


class Provider(pydantic.BaseModel):
    name: str = pydantic.Field(..., description='Name of the provider')
    description: str | None = pydantic.Field(None, description='Description of the provider')
    roles: list[str] | None = pydantic.Field(None, description='Roles of the provider')
    url: str | None = pydantic.Field(None, description='URL of the provider')


class Provenance(pydantic.BaseModel):
    providers: list[Provider]
    license: str
    license_link: LicenseLink | None = None


class Feedstock(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    title: str = pydantic.Field(..., description='Title of the feedstock')
    description: str = pydantic.Field(..., description='Description of the feedstock')
    maintainers: list[Maintainer]
    provenance: Provenance
    thumbnail: pydantic.HttpUrl | None = pydantic.Field(
        None, description='Thumbnail of the feedstock'
    )
    tags: list[str] | None = pydantic.Field(None, description='Tags of the dataset')
    links: list[Link] | None = None
    stores: list[Store] | None = None
    meta_yaml_url: pydantic.HttpUrl | None = pydantic.Field(None, alias='ncviewjs:meta_yaml_url')

    @classmethod
    def from_yaml(cls, path: str):
        content = yaml.safe_load(upath.UPath(path).read_text())
        if 'ncviewjs:meta_yaml_url' in content:
            meta_url = convert_to_raw_github_url(content['ncviewjs:meta_yaml_url'])
            meta = yaml.safe_load(upath.UPath(meta_url).read_text())
            content = content | meta
        data = cls.model_validate(content)
        return data


def convert_to_raw_github_url(github_url):
    # Check if the URL is already a raw URL
    if 'raw.githubusercontent.com' in github_url:
        return github_url

    # Replace the domain
    raw_url = github_url.replace('github.com', 'raw.githubusercontent.com')

    # Remove '/blob'
    raw_url = raw_url.replace('/blob', '')

    return raw_url
