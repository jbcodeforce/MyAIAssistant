# Knowledge Management

The platform is also able to manage knowledge and RAG content. The approach is to keep metadata about the indexed materials, and then being able to query, brainstorm, create learning path, on the index materials.

Also the RAG can be used to support task decomposition.

## Knowledge Home Page

This page lists all the link to existing content.

![](./images/km-view.png)

## Create Knowledge Entry

An entry can be a folder including a hierarchy of sub-folders with md, txt or .doc files. 

![](./images/new_km.png)

* Title, document type and source are mandatory
* When selecting a Markdown the Source can be a local file or a URL

* When selecting a website, the source is a URL

![](./images/website_new_km.png)


## Indexing the document

Once a knowledge reference is created, Clicking on the magnifier icon on the right side will start loading the content, chunk it into pieces, perform vector embedding and save the content in a vector store.

![](./images/km_indexing.png)

The completion of the processing displays a popup window with the number of chunks done.

[](./images/indexing_result.png)

## Working on Knowledge base

From the knowledge main page, clicking on `Ask AI` button will start the chat interface:

![](./images/chat_with_km.png)

And the results includes content from the newly indexed paper.

![](./images/AI_resuls_on_km.png)