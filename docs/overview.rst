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
The following is a walk-through of the important concepts in the access control
system.

Users & roles
-------------
First we have **subjects** which can be granted access to a protected resource.

- **User**: Represents an authenticated account in the system.
- **Role**: Represents a job function. Roles are created by e.g. system
  administrators and defined by a name. Users can be assigned zero or more
  roles.
- **System role**: Represents special roles that are created and defined by the
  system and automatically assigned to users (i.e. system roles cannot be
  created and defined by system administrators).

Permissions and needs
---------------------
Second, we have two entities to describe access control:

- **Need**: A need represents the smallest level of access control. It is very
  generic and can express statements such as *"has admin role"* and
  *"has read access to record 42"*.
- **Permission**: Represents a set of required *needs*, any of which should
  be fulfilled to access a resouce. E.g. a permission can combine the two
  statements above into **"has admin role or has read access to record 42"**.

The concept of a *need* can be somewhat hard to grasp at first, so let's
dive in to describe how a need is used. Essentially *needs* are used to express
a) what a permission require and b) what a user provides, i.e.:

- A permission **requires** a set of needs.
- A user **provides** a set of needs.

Thus, checking if a user can access a resource protected by a permission
amounts to checking for a non-empty **intersection** between the above sets.

Types of needs
--------------
Needs can have different types. For instance the statement *"has admin role"*
can be expressed as a *role need type* with the argument ``admin``. This means
that a permission can require the admin role need and that a user can provide
the admin role need. Some basic need types include:
