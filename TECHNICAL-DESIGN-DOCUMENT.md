# Jira Ticket to Markdown Exporter CLI – Technical Design Document

## Introduction

We propose a command-line tool **jira-download** that exports a Jira Cloud issue into a markdown file with all its attachments downloaded locally and referenced inline. The tool will use Jira’s REST API (Cloud) to retrieve the issue details (description, attachments, etc.) using an API token for authentication. It will then convert the issue’s content into GitHub-flavored Markdown and save any attached files in a local directory, adjusting the markdown so that attachment links point to the local files. This allows offline viewing or archiving of Jira tickets in a format suitable for GitHub or other Markdown readers.

**Key Features:**
- Fetch a specified Jira issue (e.g. PROJ-123) via the Jira Cloud REST API.
- Download all attachments on the issue to a local folder.
- Generate a Markdown file containing the issue’s content (description and optional metadata) with inline links/images pointing to the downloaded attachments (mirroring how they appeared in Jira).
- Operate as a CLI command (jira-download <ISSUE-KEY>) for ease of use.

## Requirements and Assumptions

* **Jira Platform:** Jira Cloud (Atlassian Cloud) is used (the solution will use the cloud REST API).
* **Authentication:** A Jira API token is available for authentication (along with the user’s email or using the token as a bearer token). We assume the user has the necessary permissions to read the issue and its attachments.
* **Input:** A single Jira issue key (like PROJ-123) provided as an argument to the CLI. (Future enhancements may allow bulk exports or additional options.)
* **Output:** A directory (named after the issue key for clarity) containing:
* A Markdown file (e.g. PROJ-123.md) with the issue content and links to attachments.
* All attachment files downloaded from the issue, saved with their original filenames.
* **Content to include:** The issue’s description (fully formatted in markdown). Basic issue metadata (like summary/title, status, type, etc.) can be included in the markdown for context (this is a “nice-to-have”). Comments or change logs are **out of scope** for the initial version (can be addressed in future versions).
* **Formatting:** Use GitHub-Flavored Markdown (GFM) for the output so that headings, lists, code blocks, tables, etc., are preserved in a readable way. Attachments that are images should be embedded with markdown image syntax, while other file types will be linked by filename. Overall, the markdown should be clean and readable (optimized for GitHub viewing).
* **“Inline attachments like Jira”:** Any images or files that were displayed inline in the Jira issue (e.g. embedded images in the description) should appear inline in the markdown as well (pointing to the local copies). Attachments not referenced in the text will be listed in an **Attachments** section. Essentially, the markdown should mimic the Jira issue’s content presentation, except that links point to local files instead of Jira’s server.
* **Environment Configuration:** The tool should allow configuration of Jira credentials (server URL, user, API token). For example, these could be supplied via environment variables or a config file (JIRA\_BASE\_URL, JIRA\_EMAIL, JIRA\_API\_TOKEN) to avoid putting secrets on the command line.

## Solution Overview

The solution will be implemented as a CLI program that performs the following high-level steps when a user runs jira-download <ISSUE-KEY>:

1. **Configuration & Auth:** Load Jira Cloud connection info (e.g. base URL like your-domain.atlassian.net) and user credentials (email & API token). Use Basic Auth with email/API token or an Authorization header with the token for API calls. (For example, using Basic Auth as email:APIToken in the HTTP request, as recommended by Atlassian[[1]](https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/#:~:text=,curl).)
2. **Issue Retrieval via API:** Call Jira’s REST API to fetch the issue data. We will use the GET /rest/api/3/issue/{ISSUE-KEY} endpoint with appropriate query parameters to retrieve the fields we need. In particular:
3. Include the **description** and **attachment** fields in the response. For example:

* GET https://<your-domain>.atlassian.net/rest/api/3/issue/PROJ-123?fields=summary,issuetype,status,description,attachment&expand=renderedFields
* This will retrieve the issue’s summary, type, status, description, attachments, etc. Adding expand=renderedFields instructs Jira to also return rendered HTML for the description (and other rich-text fields)[[2]](https://stackoverflow.com/questions/74547915/convert-jira-api-response-into-html#:~:text=I%20am%20calling%20this%20%2Frest%2Fapi%2F3%2Fissue%2F,the%20issue%20description%20in%20HTML). The raw JSON response will contain the description in Atlassian’s rich text format (known as ADF – Atlassian Document Format) under fields.description, and the rendered HTML under renderedFields.description if available. It will also contain an array of attachments under fields.attachment. Each attachment object includes details such as filename, size, and a **content URL** that can be used to download the file[[3]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post#:~:text=domain.atlassian.net%2Frest%2Fapi%2F3%2Fuser%3FaccountId%3D5b10a2844c20165700ede21g%22%20%7D%2C%20%22content%22%3A%20%22https%3A%2F%2Fyour,domain.atlassian.net%2Fjira%2Frest%2Fapi%2F3%2Fattachment%2Fthumbnail%2F10000%22).

1. **Parse Issue Data:** Once the JSON is retrieved:
2. Extract key metadata (e.g. issue key, summary/title, status, issue type, etc.). This can be used to add context at the top of the markdown (for instance, as a heading or a brief info section).
3. Extract the **description content**. If renderedFields.description (HTML) is present, use that; otherwise use fields.description (which would be in ADF JSON).
4. Extract the list of **attachments**. For each attachment, note its filename and the content URL (this URL is an API endpoint to fetch the binary content of the attachment)[[3]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post#:~:text=domain.atlassian.net%2Frest%2Fapi%2F3%2Fuser%3FaccountId%3D5b10a2844c20165700ede21g%22%20%7D%2C%20%22content%22%3A%20%22https%3A%2F%2Fyour,domain.atlassian.net%2Fjira%2Frest%2Fapi%2F3%2Fattachment%2Fthumbnail%2F10000%22). All attachments can be downloaded since we have the API token and appropriate permissions.
5. **Download Attachments:** Create a local directory for the issue (for example, ./PROJ-123/) if not already existing. For each attachment from the previous step:
6. Make an HTTP GET request to the attachment’s content URL. Use the same authentication (API token) for this request. (In Jira Cloud, this typically involves Basic Auth with email & token, or using an Authorization header. The API token in basic auth will allow direct download of the attachment content[[1]](https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/#:~:text=,curl)[[4]](https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/#:~:text=,command%20to%20download%20an%20attachment).)
7. Save the response to a file in the issue’s directory. Use the original filename as provided by Jira (e.g. if the attachment is "diagram.png", save it as diagram.png). The --create-dirs option in the curl example illustrates creating a folder per issue and saving attachments inside[[4]](https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/#:~:text=,command%20to%20download%20an%20attachment). Our tool will do this programmatically (e.g. using file I/O in the chosen language).
8. **Filename conflicts:** If two attachments coincidentally have the same name, the tool should handle this (for example, by appending a counter or the attachment ID to one of them to avoid overwrite). However, such cases are rare; we will log and adjust names if needed.
9. **Attachment types:** Identify if the attachment is an image (common types: PNG, JPG, GIF, etc.) or another file type. We will later format image attachments differently in markdown (embedded) vs. non-image (linked text). The attachment metadata includes a MIME type (e.g. "image/jpeg") which we can use[[3]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post#:~:text=domain.atlassian.net%2Frest%2Fapi%2F3%2Fuser%3FaccountId%3D5b10a2844c20165700ede21g%22%20%7D%2C%20%22content%22%3A%20%22https%3A%2F%2Fyour,domain.atlassian.net%2Fjira%2Frest%2Fapi%2F3%2Fattachment%2Fthumbnail%2F10000%22).
10. **Convert Description to Markdown:** This is a crucial step to preserve the issue’s content formatting. Jira Cloud stores rich text in ADF (JSON), but since we requested renderedFields, we have an HTML rendition of the description. We have two possible approaches here:
    a. **HTML to Markdown conversion:** Use the rendered HTML and convert it into Markdown. There are libraries and tools that can do HTML-to-Markdown conversion while preserving formatting (for example, in Python one might use html2markdown or markdownify, and in Node.js one could use turndown or similar). We will feed the HTML (which includes headings, lists, links, images, etc.) to such a converter to produce GitHub-flavored Markdown. This approach leverages Jira’s own rendering to HTML, ensuring what we convert is close to what the user sees in Jira[[2]](https://stackoverflow.com/questions/74547915/convert-jira-api-response-into-html#:~:text=I%20am%20calling%20this%20%2Frest%2Fapi%2F3%2Fissue%2F,the%20issue%20description%20in%20HTML). After conversion, we may need to do minor touch-ups (for example, ensure code blocks, tables, etc., are correctly fenced, since not all converters handle every case perfectly).
    b. **Direct ADF to Markdown conversion:** Alternatively, we could take the ADF JSON from fields.description and convert it to Markdown without going through HTML. This could be done by using a specialized library or writing a parser. There are libraries such as **adf2md** (for Node) which can convert Atlassian Document Format JSON directly into GitHub-flavored markdown[[5]](https://classic.yarnpkg.com/en/package/adf2md#:~:text=%28async%20%28%29%20%3D,ADF2MD.convert%28description). This method might preserve certain structures better (since it’s designed for ADF) and avoid any quirks of HTML conversion. However, not all node types (particularly attachments/media) are supported in some libraries[[6]](https://classic.yarnpkg.com/en/package/adf2md#:~:text=,style%20admonition), so we would still need custom handling for images/attachments.
    *Chosen approach:* For simplicity and reliability, the **HTML-to-Markdown** route is preferred initially (using expand=renderedFields). It uses Jira’s officially rendered output, which we then convert. This avoids writing a full ADF parser. We will keep the conversion logic modular so that we could swap in a direct ADF-to-MD converter in the future if needed.
11. **Inline Attachment Linking:** After converting the description to markdown, we need to ensure that any references to attachments in the text point to the local files:
12. If the description had an embedded image or attachment, the rendered HTML likely included an <img src="..."> or a hyperlink to Jira’s attachment URL. The markdown conversion might have produced something like ![ImageName](https://your-domain.atlassian.net/...) for images or [File.pdf](https://your-domain.atlassian.net/...) for links. We should post-process these links in the markdown and replace the URL with the local path (just the filename, if the markdown file is in the same directory as the attachments). For example, ![diagram.png](https://<domain>/.../attachment/content/10000) would be replaced with ![diagram.png](diagram.png). Similarly, a link [Design Doc](https://<domain>/.../content/10001) would become [Design Doc](Design%20Doc.pdf) (with proper URL-encoding for spaces if needed).
13. To implement this, we can scan the markdown text for any occurrences of the Jira attachment URL pattern or for known attachment file names. Because we have the list of all attachment filenames, one robust approach is: for each attachment, find any mention of its filename or its Jira URL in the markdown and replace it with the correct relative link to the file. This ensures all embedded references now point to local files.
14. If the description did not explicitly reference an attachment (many attachments might just be listed in Jira’s attachment section, not in the text), then there won’t be any inline link to replace for those. We will handle those in the next step.
15. **Compose the Markdown File:** Now we assemble the final markdown content. A suggested structure is:
16. A title heading that includes the issue key and summary. For example:

* # PROJ-123: Improve Login Feature
* Optionally, we can make the issue key a hyperlink to the original Jira issue (for reference), e.g. [PROJ-123](https://<your-domain>.atlassian.net/browse/PROJ-123): Improve Login Feature. This provides quick navigation back to Jira (if online), but the rest of the content will be viewable offline.

1. **Metadata section (optional):** A short section listing key fields like **Status**, **Issue Type**, **Priority**, **Assignee**, **Reporter**, etc. This can be formatted as a table or a list for clarity. For example:

* \*\*Type:\*\* Story
  \*\*Status:\*\* In Progress
  \*\*Priority:\*\* High
  \*\*Assignee:\*\* John Doe
* If metadata is not critical, this section can be minimal or omitted. However, including at least status or type can provide useful context when reading the markdown outside Jira.

1. **Description section:** The main body of the issue description, in markdown format as produced by the conversion step. We can introduce this with a subheading like ## Description (or simply start with the content if the title already implies description). All Jira formatting (headings, bold, lists, code blocks, tables, etc.) should now be reflected in proper markdown. Any images that were embedded in the description will appear as ![alt text](filename.png) referencing the downloaded file, and should render in a markdown viewer just as they did in Jira (only now loaded from local disk).
2. **Attachments section:** If there are attachments that were *not* already embedded in the description, list them here so none are missed. For example:

* ## Attachments
  - [Error Screenshot.png](Error%20Screenshot.png)
  - [AnalyticsReport.xls](AnalyticsReport.xls)
* Each attachment is listed as a bullet with a link to the local file. For image files, we might choose to embed them directly as images instead of just links, if desired. But embedding many large images might make the markdown lengthy; as a default, linking is safe, and the user can open the image as needed. For completeness, we include all attachments here (even images that were embedded) as links, or we can choose to exclude those already shown above. This is a design choice – listing all attachments ensures nothing is overlooked.

1. Ensure that the links use correct URL encoding for special characters (spaces, etc.), since in markdown a space in a link should be written as %20 or the whole link enclosed in <>. Our tool can handle this automatically or simply replace spaces with %20 in filenames for the link references. Alternatively, the program could rename files to a space-free version for convenience, but since the user likely expects original filenames, we will keep them and encode in links.
2. **Output Files and Structure:** The program will write the markdown content to a file and confirm output to the user. The structure on disk will look like:

* PROJ-123/
   ├── PROJ-123.md
   ├── attachment1.png
   ├── attachment2.docx
   └── ...
* The markdown file and attachments reside together in a folder named by the issue key. (Alternatively, we could put attachments in a subfolder like PROJ-123/attachments/ and adjust links accordingly, but for simplicity using one folder is fine.) The user can now open the markdown file in a viewer or on GitHub and see the issue content with local images displayed and file links available.

## Implementation Details

**Tech Stack:** The tool can be implemented in a language of choice that has HTTP capabilities and file system access (for example, Python, Node.js, or Go). For concreteness, we’ll describe it using Python, which has convenient libraries (requests for HTTP, markdownify or html2text for conversion, etc.). The design, however, is language-agnostic.

**Authentication:** Jira Cloud API uses Basic auth with email and API token, or Bearer token. We will use Basic Auth in our HTTP requests. This can be done by encoding email:APIToken in the Authorization header. For example, using curl:

curl --user "email@example.com:<api\_token>" https://<your-domain>.atlassian.net/rest/api/3/issue/KEY ...

This method is illustrated in Atlassian’s documentation[[1]](https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/#:~:text=,curl). In code, if using Python requests, we can do requests.get(url, auth=(email, api\_token)). We will make sure the API token and email (or an OAuth token if configured) are provided securely (via environment variables or a config file rather than plaintext arguments).

**CLI Parsing:** Use a CLI argument parser (e.g. Python’s argparse or a Node CLI library) to handle the command jira-download <ISSUE-KEY>. The user will supply the issue key. Optionally, allow flags like --output <dir> to specify a custom output directory, though by default we use the current directory or a folder named after the issue key. We might also allow a verbose flag for debugging or an option to skip downloading attachments (if needed). For now, minimal interface: just the issue key.

**Fetching the Issue:** Construct the API URL for the issue as described. We include the fields we need: at least summary, description, issuetype, status, attachment. (We can include others like priority or custom fields if needed for metadata.) Example GET request:

GET /rest/api/3/issue/PROJ-123?fields=summary,description,issuetype,status,priority,attachment&expand=renderedFields

The response will be JSON. We will parse this JSON using a JSON library. Key parts:
- fields.summary (string) – issue title.
- fields.issuetype.name – e.g. "Bug", "Story".
- fields.status.name – e.g. "To Do", "In Progress".
- fields.priority.name – e.g. "High" (if priority is used).
- fields.description – this could be a JSON object (ADF format) describing the document.
- renderedFields.description – if present, this is an HTML string of the description content, already rendered by Jira. If the issue has no description, it might be empty/None.
- fields.attachment – an array of attachment objects. Each object has filename, content (URL), mimeType, size, etc.[[3]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post#:~:text=domain.atlassian.net%2Frest%2Fapi%2F3%2Fuser%3FaccountId%3D5b10a2844c20165700ede21g%22%20%7D%2C%20%22content%22%3A%20%22https%3A%2F%2Fyour,domain.atlassian.net%2Fjira%2Frest%2Fapi%2F3%2Fattachment%2Fthumbnail%2F10000%22).

If the API call fails (e.g., unauthorized or issue not found), the tool should catch that. In case of 401 Unauthorized, inform the user to check their credentials (API token). In case of 404 Not Found, inform that the issue key doesn’t exist or is not accessible. These checks are part of robust error handling.

**Downloading Attachments:** For each attachment in the list:
- Create the output directory if it’s not already there (for the first attachment, for example).
- Build the target file path as <output-dir>/<filename>.
- Perform an HTTP GET to the attachment’s content URL. (Note: the content URL is a fully qualified link. Jira’s API returns it typically as something like https://<domain>.atlassian.net/jira/rest/api/3/attachment/content/<id>. We use this directly[[3]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post#:~:text=domain.atlassian.net%2Frest%2Fapi%2F3%2Fuser%3FaccountId%3D5b10a2844c20165700ede21g%22%20%7D%2C%20%22content%22%3A%20%22https%3A%2F%2Fyour,domain.atlassian.net%2Fjira%2Frest%2Fapi%2F3%2Fattachment%2Fthumbnail%2F10000%22). Another variant sometimes seen is a URL under /secure/attachment/<id>/...filename... – which effectively serves the same file. The provided content link is reliable for API usage.)
- Stream the response to the file (to handle large files without memory issues).
- Close the file and confirm it’s saved.
- Potential improvement: show progress or at least a log for each file (e.g. “Downloading 2 attachments… downloaded file1.png (1.2 MB)”). This feedback isn’t strictly necessary but improves user experience for large attachments.

We will also gather some info during this step that might be useful (like total attachments count, etc.) to possibly include in the markdown (e.g. “This issue has 3 attachments.”).

**Markdown Conversion:**
- If using the **HTML approach**: Take the renderedFields.description string from JSON. Pass it to an HTML-to-Markdown converter. For example, using Python’s html2text library: md\_text = html2text.html2text(description\_html). This will produce Markdown text. We might need to tweak some configurations (for instance, ensure that it treats <h1> - <h6> as #, ##, ... headings, lists properly, etc.). Many converters by default produce standard Markdown which is mostly compatible with GFM. We should verify that elements like code blocks or panels (if present) come out meaningfully. If the description has any Jira-specific content (like mentions, statuses, or macros), the HTML could include <jira-...> tags or inline images for emojis, etc. Those might be converted to something odd or left as raw HTML. We can handle these on a case-by-case basis: e.g., remove any residual HTML tags that the converter didn’t handle, or replace user mentions with plain text (the mention text is usually the user name).
- If using the **ADF direct approach**: We would use a library or write a converter. For example, the Node library adf-to-md or adf2md could be used in a Node implementation to convert the JSON directly[[5]](https://classic.yarnpkg.com/en/package/adf2md#:~:text=%28async%20%28%29%20%3D,ADF2MD.convert%28description). In Python, one could use the atlassian-python-api library’s Jira module to get the issue and possibly use its formatting (though by default it gives raw ADF). There’s also a community project pyadf for working with Atlassian Document Format. Since the HTML route is our primary plan, we won’t delve deeply here. The design will note that conversion can be swapped out.

After conversion, we have the description as a Markdown string. We then perform the **inline attachment replacement** as described earlier. Concretely, we can iterate through each attachment from the JSON and do a find-and-replace on the markdown text: replace any occurrence of the attachment’s Jira URL with the plain filename. We should also consider the case where the converter might have turned an image into a reference like ![Alt text][1] with reference-style links at bottom – depending on the converter. We will ensure to handle those by either configuring the converter to use inline links or processing reference links as well. A safe approach is simply to replace any occurrence of the known filename (when it appears as part of a URL) or the known Jira attachment base URL. Since all our attachments come from the same domain, we might do: md\_text = md\_text.replace('<your-domain>.atlassian.net/jira/rest/api/3/attachment/content/', '') and similarly for any /secure/attachment/ URLs, while being careful not to remove too much. More precisely, using a regex to find markdown image or link patterns containing our Jira domain and replacing with the filename might be best. This ensures embedded images now point correctly to local files.

**Constructing the Markdown file content:** We combine the pieces:
- Start with the **title** as a level-1 heading. Use the format # KEY: Summary. We pull fields.summary from the JSON for this. (If summary is empty for some reason, just use the key). Optionally, hyperlink the key to the Jira issue URL.
- Follow with a brief **metadata block**. We can format this as a small table or list. For simplicity, a list of bold-field names is fine (as shown earlier). We include those fields which are readily available and make sense to a reader. Common ones: **Status**, **Type**, **Priority**, **Assignee**, **Reporter**, **Created date**, **Updated date**. All these are available in the JSON (fields.status.name, fields.issuetype.name, fields.priority.name, fields.assignee.displayName, etc.). Since the user indicated metadata is not critical, we might include just a couple of these for now. The design allows extension to include more if needed.
- Add a horizontal rule or an empty line, then the **Description** content (the markdown we converted). If it’s long, it will naturally span multiple lines/paragraphs as needed. This content is the core of the issue. It may contain its own headings, lists, etc., which we preserve.
- Finally, if there are attachments (we have the list): add an **Attachments** section as a subheading. List each attachment with a markdown link. If some attachments (like images) were already shown above, we might still list them here for completeness, or we can choose to list only those not appearing above to avoid duplication. This can be decided by checking if the filename was found in the description text. For thoroughness, we’ll list all. The link text can simply be the filename (or we could use a more descriptive name if available, but filename is straightforward).

**Example Markdown Output (illustrative):**

# PROJ-123: Improve Login Feature

\*\*Type:\*\* Story &nbsp;&nbsp; \*\*Status:\*\* In Progress &nbsp;&nbsp; \*\*Priority:\*\* High
\*\*Assignee:\*\* Jane Doe &nbsp;&nbsp; \*\*Reporter:\*\* John Smith

## Description

Our login feature needs to support SSO via OAuth2. This is \*critical\* for enterprise customers.
The main requirements are:
- Integrate with OAuth2 providers (Google, Microsoft).
- Fall back to local authentication if OAuth2 fails.

Below is the proposed UI flow:

![Login Screen Mockup](login\_mock.png)

As shown above, the "SSO Login" button will appear on the login page... (etc.)

## Attachments

- [login\_mock.png](login\_mock.png)
- [ErrorLogs.txt](ErrorLogs.txt)

In this example, login\_mock.png was embedded in the description (as an image), so it appears inline where it was referenced, and we also list it under attachments. The second file ErrorLogs.txt was just attached but not referenced in text, so it only appears in the attachments list.

**Local Links in Markdown:** Note that in the markdown, we used relative paths like (login\_mock.png). Since the markdown file is in the same directory as the image, this will correctly load the image when viewed on GitHub or a local MD viewer. If we had put attachments in a subdirectory, the link would be e.g. (attachments/login\_mock.png) accordingly. We ensure consistency between how we save files and how we reference them.

## Testing and Validation

To ensure the tool works as expected:
- Test with issues that have various content: plain text description, rich text (headings, lists), images, and multiple attachments of different types. Verify that after running the tool, the markdown looks correct (open it in a viewer or VSCode preview to check formatting) and that images display from the local files.
- Test an issue with no description (edge case: the markdown should still be created, perhaps with just metadata and attachments list).
- Test with an issue that has no attachments (just ensure it doesn’t error out and simply produces the markdown without an attachments section or with an empty section).
- Verify that authentication works (e.g. provide a wrong token to see if it fails gracefully with an error message).
- If possible, test on a private project and a project where the user’s permissions are limited, to ensure the tool properly handles “403 Forbidden” if it arises (and communicates to the user).
- Performance is generally not a concern for single-issue export (the payloads are small, maybe a few hundred KB plus attachment sizes). If an issue had a very large attachment (hundreds of MB), the download should still work but we might want to note progress or at least not freeze the UI. This can be handled with streaming as mentioned.

## Future Enhancements (Day 2 Requirements)

This design lays the foundation for additional features to be added later:
- **Include Comments:** We can extend the tool to also fetch comments on the issue (using the issue/<key>/comment API or by adding expand=comments in some cases) and append them to the markdown. Each comment could be formatted as a blockquote or a section with the comment author and date, similar to how Jira presents them. This would provide a full archive of the issue’s discussion. (Since comments themselves are stored in ADF as well, we would convert them to markdown in the same way as the description, possibly reusing the conversion logic[[7]](https://github.com/ankitpokhrel/jira-cli#:~:text=).)
- **Multiple Issues or Bulk Export:** The CLI could accept a list of issue keys or a JQL query to export multiple issues in one go (e.g., a whole epic or sprint). This would involve looping over issues, possibly rate-limiting the API calls if needed.
- **Hierarchical Export:** For an epic issue, automatically fetch its stories, or for a story, fetch sub-tasks, etc., writing them to a structured set of markdown files (this starts to become more like a static site of the project’s issues).
- **Better ADF handling:** We might implement a more robust conversion for Jira’s content. For example, handle any Atlassian-specific content that the basic HTML conversion skipped – such as Jira Issue mention links (which in HTML might appear as just a hyperlink to another issue), status lozenges, or user mentions. We could replace those in markdown with plain text (e.g., issue keys or user names).
- **Attachments in Comments:** Ensure that if comments have attachments (images added in comments), those are also downloaded and referenced. This would require scanning comment bodies for attachment URLs similarly.
- **Pluggable Output Format:** While our focus is Markdown, the same data could potentially be exported to other formats (HTML, AsciiDoc, etc.) with different converters. Designing the conversion step to be modular allows such flexibility.
- **Use of Jira API libraries:** In the future, we might integrate a Jira client library to simplify some of the REST calls (for example, the official Python jira library can fetch issues and attachments easily). However, using the direct REST calls as we did gives fine-grained control and less dependency bloat – which is why we chose it as “the right way” for this scenario.

## Conclusion

This technical design specifies a robust approach to implement a **Jira Ticket to Markdown Exporter** CLI tool. By leveraging Jira’s REST API and carefully converting content to GitHub-flavored markdown, the tool will produce a local, self-contained representation of a Jira issue (including attachments) that can be viewed or shared outside of Jira. The design emphasizes correctness (using official APIs[[3]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post#:~:text=domain.atlassian.net%2Frest%2Fapi%2F3%2Fuser%3FaccountId%3D5b10a2844c20165700ede21g%22%20%7D%2C%20%22content%22%3A%20%22https%3A%2F%2Fyour,domain.atlassian.net%2Fjira%2Frest%2Fapi%2F3%2Fattachment%2Fthumbnail%2F10000%22), preserving formatting) and maintainability (clear steps that can be extended to comments or multiple issues later). With this design, a developer can proceed to implement the CLI tool, confident that it will meet the requirements of exporting Jira tickets “the right way.”

**Sources:** The approach relies on Atlassian’s documented API capabilities for retrieving issues and attachments. For example, Jira’s REST API returns attachment metadata including content download links[[3]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post#:~:text=domain.atlassian.net%2Frest%2Fapi%2F3%2Fuser%3FaccountId%3D5b10a2844c20165700ede21g%22%20%7D%2C%20%22content%22%3A%20%22https%3A%2F%2Fyour,domain.atlassian.net%2Fjira%2Frest%2Fapi%2F3%2Fattachment%2Fthumbnail%2F10000%22), and supports API token authentication for scripts[[1]](https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/#:~:text=,curl). We also utilize the Jira API’s ability to render fields like description to HTML for easy conversion[[2]](https://stackoverflow.com/questions/74547915/convert-jira-api-response-into-html#:~:text=I%20am%20calling%20this%20%2Frest%2Fapi%2F3%2Fissue%2F,the%20issue%20description%20in%20HTML). Open-source tools and libraries (e.g., for ADF to Markdown conversion[[5]](https://classic.yarnpkg.com/en/package/adf2md#:~:text=%28async%20%28%29%20%3D,ADF2MD.convert%28description)) informed our strategy but the core logic is implemented within our own program. This ensures the solution is self-contained and can be adapted as needed for the user’s environment.

[[1]](https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/#:~:text=,curl) [[4]](https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/#:~:text=,command%20to%20download%20an%20attachment) How to Export Attachments from Jira Cloud Projects via REST API | Jira and Jira Service Management | Atlassian Support

<https://support.atlassian.com/jira/kb/export-jira-project-attachments-using-rest-api/>

[[2]](https://stackoverflow.com/questions/74547915/convert-jira-api-response-into-html#:~:text=I%20am%20calling%20this%20%2Frest%2Fapi%2F3%2Fissue%2F,the%20issue%20description%20in%20HTML) php - Convert jira API response into HTML - Stack Overflow

<https://stackoverflow.com/questions/74547915/convert-jira-api-response-into-html>

[[3]](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post#:~:text=domain.atlassian.net%2Frest%2Fapi%2F3%2Fuser%3FaccountId%3D5b10a2844c20165700ede21g%22%20%7D%2C%20%22content%22%3A%20%22https%3A%2F%2Fyour,domain.atlassian.net%2Fjira%2Frest%2Fapi%2F3%2Fattachment%2Fthumbnail%2F10000%22) The Jira Cloud platform REST API

<https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/>

[[5]](https://classic.yarnpkg.com/en/package/adf2md#:~:text=%28async%20%28%29%20%3D,ADF2MD.convert%28description) [[6]](https://classic.yarnpkg.com/en/package/adf2md#:~:text=,style%20admonition) adf2md | Yarn

<https://classic.yarnpkg.com/en/package/adf2md>

[[7]](https://github.com/ankitpokhrel/jira-cli#:~:text=) GitHub - ankitpokhrel/jira-cli: Feature-rich interactive Jira command line.

<https://github.com/ankitpokhrel/jira-cli>
