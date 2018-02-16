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


Usage
=====

To demonstrate the usage of invenio-pidrelations we'll use the versioning example.
First we will create a deposit, mint its PID and the parent PID and finally populate the versioning node.

.. code-block:: python

    from invenio_pidrelations.contrib.versioning import PIDNodeVersioning
    from invenio_deposit.api import Deposit
    from invenio_pidstore.providers.recordid import RecordIdProvider

    # create a new deposit
    new_deposit = Deposit.create({...})
    # create the parent PID
    parent_pid = RecordIdProvider.create(...,
                                         status=PIDStatus.REGISTERED,
                                         ...).pid
    # create the PID of the new_deposit 
    provider = RecordIdProvider.create('dep', new_deposit.id)
    # create the versioning node, set the pid to the parent_pid
    versioning_node = PIDNodeVersioning(pid=parent_pid)
    # add the new_record PID to the node as a child
    versioning_node.insert_draft_child(child_pid=provider.pid)

The result will have the following structure:

.. graphviz::

    digraph {
        {
            "ParentPID" [ xlabel = "Registered" ];
        }   
        "ParentPID" -> "Draft" [ label = "record_draft", style = "dotted" ];
    }

When the first draft is published the parent PID status changes from Registered to Redirected, and now resolves to version 1.

.. graphviz::

    digraph {
        {
            "ParentPID" [ xlabel = "Redirected", style = "bold" ];
            "Version1" [ style = "bold" ];
        }
        "ParentPID" -> "Version1" [ label = "version", style = "bold" ];
    }

The PIDNodeVersioning class used here has presets for the maximum number of parents and children, specifically it is set to 1 parent maximum and unlimited chilren.
If one needs to create PID relations with different limits on the parent and children, the PIDNodeOrdered class can be used instead with different `max_parents` and `max_children` attributes in its constructor.
For all PID relations classes there can be only a single draft child for each version chain.
By default deleted versions are not removed from the chain to maintain the history of a record.

Serializers
-----------

In order to save the relations between records and make them indexable, a serializer is used to print out all relations of a given PID.
These are stored in Elasticsearch in the json form.
