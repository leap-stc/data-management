# What is the LEAP Data Catalog?

The LEAP Data Catalog is a centralized repository that consolidates various LEAP datasets into a single JSON file. This JSON catalog is generated from individual YAML files, each representing a dataset. These YAML files are located in [datasets](./datasets) directory. This catalog is currently in development and a draft version is available at <https://leap-data-catalog.vercel.app/>.

## The Schema

The catalog uses a schema defined in [schema.json](./validator/schema.json). The schema is also available in [schema.yaml](./validator/schema.yaml) and [schema.py](./validator/schema.py). The schema is validated using the Pydantic library.

Here are some key fields you will need to include in your dataset YAML file:

### Required Fields

| Field         | Type             | Description                                    | Object Properties                                                                                                    |
| ------------- | ---------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `name`        | String           | The name of the dataset.                       |                                                                                                                      |
| `description` | String           | A brief description of the dataset.            |                                                                                                                      |
| `stores`      | Array of Objects | Information about where the dataset is stored. | `name`: Name of the store (Type: String)<br>`href`: URL of the store (Type: String, Format: URI)                     |
| `maintainers` | Array of Objects | Information about the dataset's maintainers.   | `name`: Name of the maintainer (Type: String)<br>`github_username`: GitHub username of the maintainer (Type: String) |

### Optional Fields

| Field          | Type             | Description                              | Object Properties                                                                                    |
| -------------- | ---------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `thumbnail`    | String           | Thumbnail of the dataset.                |                                                                                                      |
| `license`      | Object           | Information about the dataset's license. | `name`: Name of the license (Type: String)<br>`href`: URL of the license (Type: String, Format: URI) |
| `tags`         | Array of Strings | Tags associated with the dataset.        |                                                                                                      |
| `links`        | Array of Objects | Additional links related to the dataset. | `label`: Label of the link (Type: String)<br>`href`: URL of the link (Type: String, Format: URI)     |
| `doi_citation` | String           | DOI citation for the dataset.            |                                                                                                      |
| `demo`         | Boolean          | Whether the dataset is a demo.           |                                                                                                      |

Note: The fields `name`, `description`, `stores`, and `maintainers` are mandatory. You can find the full schema [here](./validator/schema.json).

## How to add a new dataset

### Step 1: Create a new YAML file

Navigate to the [`catlog/datasets`](./datasets/) directory and create a new YAML file. Name the file after your dataset—like `my-awesome-dataset.yaml`.

Here's a sample YAML file to guide you:

```yaml
# my-awesome-dataset.yaml
name: "Climate Change Data"
description: "This dataset contains global temperature, CO2 levels, and sea level rise data."
stores:
  - name: "AWS S3"
    href: "https://aws.amazon.com/s3/"
  - name: "Google Cloud Storage"
    href: "https://cloud.google.com/storage"
maintainers:
  - name: "John Doe"
    github_username: "johndoe"
thumbnail: "https://example.com/thumbnail.jpg"
license:
  name: "MIT"
  href: "https://opensource.org/licenses/MIT"
tags:
  - "Climate"
  - "Temperature"
  - "Sea Level"
links:
  - label: "Data Source"
    href: "https://example.com/data_source"
  - label: "Documentation"
    href: "https://example.com/docs"
doi_citation: "https://doi.org/10.xxxxx/yyyyy"
demo: false
```

### Step 2: Local Validation

It's always good to validate your YAML file against the schema locally before creating a pull request. This ensures that your dataset meets all the criteria.

1. **Install Dependencies**: Make sure you have the required Python packages installed. The list is in [`ci/environment.yaml`](../ci/environment.yaml).
2. **Run the Validator**: Go to the [`catalog/validator`](./validator/) directory and run:

```bash
python validate.py --path ../datasets
```

If all is well, you'll see a success message. If not, you'll get an error output, which you'll need to fix.

### Step 3: Create a Pull Request

1. **Fork the Repository**: Fork this repository to your GitHub account.
2. **Clone the Fork**: Clone it to your local machine.
3. **Branch**: Create a new branch for your dataset.
4. **Commit**: Add your YAML file and commit the changes.
5. **Push**: Push the changes to your fork.
6. **Pull Request**: Create a new pull request against the main repository.

### What Happens Next?

Once your pull request is in, our GitHub Actions will automatically validate your YAML file against the schema. If all checks pass, your dataset will be added to the consolidated JSON catalog, which is then rendered at <https://leap-data-catalog.vercel.app/> after the pull request is merged.
