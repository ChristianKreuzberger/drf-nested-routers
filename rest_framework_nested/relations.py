"""
Serializer fields that deal with relationships with nested resources.

These fields allow you to specify the style that should be used to represent
model relationships with hyperlinks.
"""
from __future__ import unicode_literals

import rest_framework.relations


class NestedHyperlinkedRelatedField(rest_framework.relations.HyperlinkedRelatedField):
    lookup_field = 'pk'
    parent_lookup_field = 'parent'
    parent_lookup_related_field = 'pk'

    def __init__(self, *args, **kwargs):
        self.parent_lookup_field = kwargs.pop('parent_lookup_field', self.parent_lookup_field)
        self.parent_lookup_url_kwarg = kwargs.pop('parent_lookup_url_kwarg', self.parent_lookup_field)
        self.parent_lookup_related_field = kwargs.pop('parent_lookup_related_field', self.parent_lookup_related_field)
        super(NestedHyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk is None:
            return None

        lookup_value = getattr(obj, self.lookup_field)
        parent_lookup_object = getattr(obj, self.parent_lookup_field)
        parent_lookup_value = getattr(
            parent_lookup_object,
            self.parent_lookup_related_field
        ) if parent_lookup_object else None

        kwargs = {
            self.lookup_url_kwarg: lookup_value,
            self.parent_lookup_url_kwarg: parent_lookup_value,
        }
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.

        Takes the matched URL conf arguments, and should return an
        object instance, or raise an `ObjectDoesNotExist` exception.
        """
        lookup_value = view_kwargs[self.lookup_url_kwarg]
        parent_lookup_value = view_kwargs[self.parent_lookup_url_kwarg]
        lookup_kwargs = {
            self.lookup_field: lookup_value,
            self.parent_lookup_field: parent_lookup_value,
        }
        return self.get_queryset().get(**lookup_kwargs)


class HyperlinkedRouterField(rest_framework.relations.HyperlinkedRelatedField):
    """
    A field that represents the nested router URL for an object relation.

    This is in contrast to `NestedHyperlinkedRelatedField` which represents the
    nested URLs of relationships to other objects.
    """

    def __init__(self, view_name=None, **kwargs):
        kwargs['many'] = False
        super(HyperlinkedRouterField, self).__init__(view_name, **kwargs)

    def get_queryset(self):
        if not self.queryset:
            model = self.parent.Meta.model
            self.queryset = getattr(model, self.source).related
        super(HyperlinkedRouterField, self).get_queryset()

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, self.lookup_field) \
                and getattr(obj, self.lookup_field) is None:
            return None
        if hasattr(obj, 'instance') \
                and hasattr(obj.instance, self.lookup_field) \
                and getattr(obj.instance, self.lookup_field) is None:
            return None

        if isinstance(obj, rest_framework.relations.PKOnlyObject):
            lookup_value = getattr(self.root.instance, self.lookup_field)
        elif hasattr(obj, self.lookup_field):
            lookup_value = getattr(obj, self.lookup_field)
        elif hasattr(obj.instance, self.lookup_field):
            lookup_value = getattr(obj.instance, self.lookup_field)
        else:
            return None

        kwargs = {self.lookup_url_kwarg: lookup_value}
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)
