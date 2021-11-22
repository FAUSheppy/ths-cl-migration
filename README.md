# Migration Tool for docx-Databases
In the early 2000s it used to be common to use a database function in the doc/docx document-standard as source for data in MS-Office macro. For example, maintain a list of customers in such a "database" and use it to automatically populate letters and invoices based on project id's.

Now this approach has various drawbacks, including:

- it's incredibly slow
- it's loaded to memory in whole every time it's used
- newer MS-Office version don't allow you to use it over the network by default
- it's hard to maintain
- it does not support advanced queries

# Nginx Configuration

# config explanation

---

This project aims to create a pipeline to migrate away from this obsolete technology, and use a real database and easy to use web-interface.
