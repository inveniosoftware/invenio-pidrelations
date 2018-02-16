..
    This file is part of Invenio.
    Copyright (C) 2017 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.


Overview
========

The following is a walk-through of the important concepts and applications of
PID relations.

Pesistent Identifiers
---------------------

Persistent identifiers map an external persistent identifier into an internal resource.
One can interact with them through the [invenio-pidstore](https://github.com/inveniosoftware/invenio-pidstore) API.
There are many scenarios where persistent identifiers have to connect, as records can have various relations.
A way to represent this internally is by translating the PIDs to nodes and the relations to edges between them.
This module provides the tools for creating this mechanism.
There are different classes which can be used as building blocks for different applications and needs.
Two direct applications of the functionality are record versioning and record collections.
An example implementation of record versioning is described in the Usage section.

Relations
---------

Relations refer to the type of connections that two persistent identifiers can have.
Two are provided out of the box, the `version` relation and the `record_draft`.
Both are applied for record versioning, the former refers to the relation between the master version of a record and a specific version while the latter to the relation between the master version and a draft for a new record version.


.. graphviz::

    digraph {
    	{
    		"ParentPID" [ style = "bold" ];
    		"Version1";
    		"Version2";
    		"Version3" [ style = "bold" ];
    	}
      "ParentPID" -> "Version1" [ label = "version" ];
      "ParentPID" -> "Version2" [ label = "version" ];
      "ParentPID" -> "Version3" [ label = "version", style = "bold" ];
    }

The ParentPID node doesn't represent a specific version of a record but the record chain in whole. By defaul it redirects to the last published version of a record. In the graph above that is version 3.

.. graphviz::

    digraph {
    	{
    		"ParentPID" [ style = "bold" ];
    		"Version1";
    		"Version2";
    		"Version3" [ style = "bold" ];
    	}
      "ParentPID" -> "Version1" [ label = "version" ];
      "ParentPID" -> "Version2" [ label = "version" ];
      "ParentPID" -> "Version3" [ label = "version", style = "bold" ];
      "ParentPID" -> "Draft" [ label = "record_draft", style = "dotted" ];
    }

The procedure of creating a new record version starts at the deposit stage, which adds the draft record node to the chain as seen above.

