#
# Katello Organization actions
# Copyright 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

import os

from katello.client.api.content_view_definition import ContentViewDefinitionAPI
from katello.client.api.filter import FilterAPI
from katello.client.cli.base import opt_parser_add_org, opt_parser_add_product
from katello.client.core.base import BaseAction, Command
from katello.client.api.utils import get_repo, get_cv_definition, ApiDataError, \
    get_filter
from pprint import pformat
# base filter action ----------------------------------------

class FilterAction(BaseAction):

    def __init__(self):
        super(FilterAction, self).__init__()
        self.api = FilterAPI()

    @classmethod
    def _add_cvd_filter_opts(cls, parser):
        parser.add_option('--definition', dest='definition_name',
                help=_("content view definition name eg: def1"))
        parser.add_option('--definition_label', dest='definition_label',
                help=_("content view definition label eg: def1"))
        parser.add_option('--definition_id', dest='definition_id',
                help=_("content view definition id eg: 1"))

    @classmethod
    def _add_get_filter_opts(cls, parser):
        FilterAction._add_cvd_filter_opts(parser)
        parser.add_option('--name', dest='name',
                help=_("filter name eg: 'package filter acme'"))
        parser.add_option('--id', dest='id',
                help=_("filter id eg: 42"))

    @classmethod
    def _add_filter_opts_check(cls, validator):
        validator.require_at_least_one_of(('name', 'id'))
        validator.mutually_exclude('name', 'id')

    @classmethod
    def _add_cvd_opts_check(cls, validator):
        validator.require_at_least_one_of(('definition_name', 'definition_label', 'definition_id'))
        validator.mutually_exclude('definition_name', 'definition_label', 'definition_id')

# filter actions -----------------------------------------------------

class List(FilterAction):

    description = _('list known filters for a given content view definition')

    def setup_parser(self, parser):
        self._add_cvd_filter_opts(parser)
        opt_parser_add_org(parser, required=1)

    def check_options(self, validator):
        validator.require(('org'))
        self._add_cvd_opts_check(validator)

    def run(self):
        org_name = self.get_option('org')
        definition_label = self.get_option('definition_label')
        definition_name = self.get_option('definition_name')
        definition_id = self.get_option('definition_id')

        definition = get_cv_definition(org_name, definition_label,
                                       definition_name, definition_id)
        defs = self.api.filters_by_cvd_and_org(definition["id"], org_name)

        self.printer.add_column('id', _("ID"))
        self.printer.add_column('name', _("Name"))
        self.printer.add_column('content_view_definition_label', _("Content View Definition"))
        self.printer.add_column('organization', _('Org'))

        self.printer.set_header(_("Content View Definition Filters"))
        self.printer.print_items(defs)
        return os.EX_OK


class Info(FilterAction):
    description = _('list a specific filter')

    @classmethod
    def rules_formatter(cls, rules):
        ret = list()
        for rule in rules:
            item = list()
            item.append(_("Id") + ": " + str(rule["id"]))
            item.append(_("Content") + ": " + rule["content"])
            item.append(_("Type") + ": " + (rule["inclusion"] and "includes" or "excludes") )
            item.append(_("Rule") + ": ")
            item.append(" " + pformat(rule["rule"]))
            ret.append("\n".join(item))
            ret.append("\n")
        return "\n".join(ret)

    def setup_parser(self, parser):
        self._add_get_filter_opts(parser)
        opt_parser_add_org(parser, required=1)

    def check_options(self, validator):
        validator.require(('org'))
        self._add_filter_opts_check(validator)
        self._add_cvd_opts_check(validator)

    def run(self):
        org_name = self.get_option('org')
        filter_name = self.get_option('name')
        filter_id = self.get_option('id')
        definition_label = self.get_option('definition_label')
        definition_name = self.get_option('definition_name')
        definition_id = self.get_option('definition_id')

        definition = get_cv_definition(org_name, definition_label,
                                       definition_name, definition_id)

        # this'll check that filter_id exists and if not, display a user-friendly message
        filter_id = get_filter(org_name, definition["id"], filter_name, filter_id)["id"]

        cvd_filter = self.api.get_filter_info(filter_id, definition["id"], org_name)

        self.printer.add_column('id', _("ID"))
        self.printer.add_column('name', _("Name"))
        self.printer.add_column('content_view_definition_label', _("Content View Definition"))
        self.printer.add_column('organization', _('Org'))
        self.printer.add_column('products', _("Products"), multiline=True)
        self.printer.add_column('repos', _("Repos"), multiline=True)
        self.printer.add_column('rules', _("Rules"), multiline=True, value_formatter = Info.rules_formatter)
        self.printer.set_header(_("Content View Definition Filter Info"))
        self.printer.print_item(cvd_filter)
        return os.EX_OK

class Create(FilterAction):
    description = _('create a filter')
    def setup_parser(self, parser):
        self._add_get_filter_opts(parser)
        opt_parser_add_org(parser, required=1)

    def check_options(self, validator):
        validator.require(('org', 'name'))
        self._add_cvd_opts_check(validator)

    def run(self):
        org_name = self.get_option('org')
        filter_name = self.get_option('name')
        definition_label = self.get_option('definition_label')
        definition_name = self.get_option('definition_name')
        definition_id = self.get_option('definition_id')

        definition = get_cv_definition(org_name, definition_label,
                                       definition_name, definition_id)

        self.api.create(filter_name, definition["id"], org_name)
        print _("Successfully created filter [ %s ]") % filter_name
        return os.EX_OK

class Delete(FilterAction):

    description = _('delete a filter')

    def setup_parser(self, parser):
        self._add_get_filter_opts(parser)
        opt_parser_add_org(parser, required=1)

    def check_options(self, validator):
        validator.require(('org'))
        self._add_filter_opts_check(validator)
        self._add_cvd_opts_check(validator)

    def run(self):
        org_name = self.get_option('org')
        filter_name = self.get_option('name')
        filter_id = self.get_option('id')
        definition_label = self.get_option('definition_label')
        definition_name = self.get_option('definition_name')
        definition_id = self.get_option('definition_id')

        definition = get_cv_definition(org_name, definition_label,
                                       definition_name, definition_id)
        cvd_filter = get_filter(org_name, definition["id"], filter_name, filter_id)
        self.api.delete(cvd_filter["id"], definition["id"], org_name)

        print _("Successfully deleted filter [ %s ]") % filter_name
        return os.EX_OK

class AddRemoveProduct(FilterAction):
    addition = True

    @property
    def description(self):
        if self.addition:
            return _('add a product to a filter')
        else:
            return _('remove a product from a filter')

    def __init__(self, addition):
        super(AddRemoveProduct, self).__init__()
        self.addition = addition

    def setup_parser(self, parser):
        opt_parser_add_org(parser, required=1)
        opt_parser_add_product(parser, required=1)
        self._add_get_filter_opts(parser)

    def check_options(self, validator):
        validator.require(('org'))
        self._add_filter_opts_check(validator)
        validator.require_at_least_one_of(('product', 'product_label', 'product_id'))
        validator.mutually_exclude('product', 'product_label', 'product_id')
        self._add_cvd_opts_check(validator)

    def run(self):
        org_name = self.get_option('org')
        filter_name = self.get_option('name')
        filter_id = self.get_option('id')
        product_name = self.get_option('product')
        product_id = self.get_option('product_id')
        product_label = self.get_option('product_label')
        definition_label = self.get_option('definition_label')
        definition_name = self.get_option('definition_name')
        definition_id = self.get_option('definition_id')
        cvd = get_cv_definition(org_name, definition_label,
                                definition_name, definition_id)

        product = self.identify_product(cvd, product_name, product_label, product_id)

        cvd_filter = get_filter(org_name, cvd["id"], filter_name, filter_id)
        products = self.api.products(cvd_filter["id"], cvd["id"], org_name)
        products = [f['id'] for f in products]

        self.update_products(org_name, cvd["id"], cvd_filter, products, product)
        return os.EX_OK

    def update_products(self, org_name, cvd, cvd_filter, products, product):
        if self.addition:
            products.append(product['id'])
            message = _("Added product [ %(prod)s ] to filter [ %(filter)s ]" % \
                        ({"prod": product['label'], "filter": cvd_filter["name"]}))
        else:
            products.remove(product['id'])
            message = _("Removed product [ %(prod)s ] from filter [ %(filter)s ]" %
                        ({"prod": product['label'], "filter": cvd_filter["name"]}))

        self.api.update_products(cvd_filter["id"], cvd, org_name, products)
        print message

    def identify_product(self, cvd, product_name, product_label, product_id):
        org_name = self.get_option('org')
        cvd_api = ContentViewDefinitionAPI()
        cvd_products = cvd_api.all_products(org_name, cvd["id"])

        products = [prod for prod in cvd_products if prod["id"] == product_id \
                             or prod["name"] == product_name or prod["label"] == product_label]

        if len(products) > 1:
            raise ApiDataError(_("More than 1 product found with the name or label provided, "\
                                 "recommend using product id.  The product id may be retrieved "\
                                 "using the 'product list' command."))
        elif len(products) == 0:
            raise ApiDataError(_("Could not find product [ %s ] within organization [ %s ] and definition [%s] ") %
                               ((product_name or product_label or product_id), org_name, cvd["name"]))

        return products[0]


class AddRemoveRepo(FilterAction):

    select_by_env = False
    addition = True

    @property
    def description(self):
        if self.addition:
            return _('add a repo to a filter')
        else:
            return _('remove a repo from a filter')

    def __init__(self, addition):
        super(AddRemoveRepo, self).__init__()
        self.addition = addition

    def setup_parser(self, parser):
        opt_parser_add_org(parser, required=1)
        parser.add_option('--repo', dest='repo',
                          help=_("repository name (required)"))
        parser.add_option('--product', dest='product',
                          help=_("product name (product name, label or id required)"))
        parser.add_option('--product_label', dest='product_label',
                          help=_("product label (product name, label or id required)"))
        parser.add_option('--product_id', dest='product_id',
                          help=_("product id (product name, label or id required)"))
        self._add_get_filter_opts(parser)

    def check_options(self, validator):
        validator.require(('org', 'repo'))
        self._add_filter_opts_check(validator)
        validator.require_at_least_one_of(('product', 'product_label', 'product_id'))
        validator.mutually_exclude('product', 'product_label', 'product_id')
        self._add_cvd_opts_check(validator)

    def run(self):
        org_name = self.get_option('org')
        filter_name = self.get_option('name')
        filter_id = self.get_option('id')
        repo_name = self.get_option('repo')
        product = self.get_option('product')
        product_label = self.get_option('product_label')
        product_id = self.get_option('product_id')
        definition_label = self.get_option('definition_label')
        definition_name = self.get_option('definition_name')
        definition_id = self.get_option('definition_id')

        definition = get_cv_definition(org_name, definition_label,
                                       definition_name, definition_id)

        cvd_filter = get_filter(org_name, definition["id"], filter_name, filter_id)

        repo = get_repo(org_name, repo_name, product, product_label, product_id)
        repos = self.api.repos(cvd_filter["id"], definition["id"], org_name)
        repos = [f['id'] for f in repos]

        self.update_repos(org_name, definition["id"], cvd_filter, repos, repo)

        return os.EX_OK

    def update_repos(self, org_name, cvd_id, cvd_filter, repos, repo):
        if self.addition:
            repos.append(repo["id"])
            message = _("Added repository [ %s ] to filter [ %s ]" % \
                        (repo["name"], cvd_filter["name"]))
        else:
            repos.remove(repo["id"])
            message = _("Removed repository [ %s ] from filter [ %s ]" % \
                        (repo["name"], cvd_filter["name"]))

        self.api.update_repos(cvd_filter["id"], cvd_id, org_name, repos)
        print message

class AddRule(FilterAction):
    content_types = ["rpm", "package_group", "erratum", "puppet_module"]
    inclusion_types = ["includes", "excludes"]
    default_inclusion_type = "includes"
    @property
    def description(self):
        return _('add a rule to a filter')

    def __init__(self):
        super(AddRule, self).__init__()

    def setup_parser(self, parser):
        opt_parser_add_org(parser, required=1)
        parser.add_option('--rule', dest='rule',
                          help=_("a specification of the rule in json format (required)"))
        parser.add_option('--content', dest='content', type="choice",
                        choices = self.content_types,
            help=_("content type of the rule (choices: [%s], default: none)") %\
                                                        ", ".join(self.content_types))
        parser.add_option('--type', dest='inclusion', default = self.default_inclusion_type,
            help=_("inclusion type of the rule (choices: [%s], default: %s)") %\
                            (", ".join(self.inclusion_types), self.default_inclusion_type))
        parser.enable_epilog_formatter(False)
        parser.epilog = AddRule._epilog()
        self._add_get_filter_opts(parser)

    def check_options(self, validator):
        validator.require(('rule', 'org', 'content'))
        self._add_filter_opts_check(validator)
        self._add_cvd_opts_check(validator)

    def run(self):
        org_name = self.get_option('org')
        filter_name = self.get_option('name')
        filter_id = self.get_option('id')
        rule = self.get_option('rule')
        definition_label = self.get_option('definition_label')
        definition_name = self.get_option('definition_name')
        definition_id = self.get_option('definition_id')
        content = self.get_option('content')
        inclusion = ("includes" == self.get_option('inclusion'))
        definition = get_cv_definition(org_name, definition_label,
                                       definition_name, definition_id)
        cvd_filter = get_filter(org_name, definition["id"], filter_name, filter_id)

        self.api.create_rule(cvd_filter["id"], definition["id"], org_name, rule, content, inclusion)
        print _("Successfully created rule [ %s ]") % rule
        return os.EX_OK

    @classmethod
    def _epilog(cls):
        epilog = list()
        epilog.append(_("Rule specification for content types."))
        epilog.append(_("Package") + ": (rpm)")
        epilog.append(_("Specification"))
        epilog.append("""{"units":<["name", "version", "min_version", "max_version"]*>}""")
        example = {"units":[{"name": "pulp-client", "version": "2.0.7"}, \
                        {"name": "pulp-adm*", "min_version": "2.0.4", "max_version": "2.0.8"}]}
        epilog.append(_("Examples"))
        epilog.append(pformat(example))
        epilog.append("")
        epilog.append(_("Package Group") + ": (package_group)")
        epilog.append(_("Specification"))
        epilog.append("""{"units":<["name"]*>}""")

        epilog.append(_("Examples"))
        example = {"units":[{"name": "group1"}, {"name": "group-foo*"}]}
        epilog.append(pformat(example))
        epilog.append("")

        epilog.append(_("Errata") + ": (erratum)")
        epilog.append(_("Specification"))
        epilog.append("""{"units":<["id"]*>} |""" + \
                        """ {"date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}} |""" + \
                        """ {"errata_type" : [< "enhancement", "security", "bugfix">*]}""")
        epilog.append(_("Examples"))
        epilog.append(_("By Id"))
        example = {"units":[{"id": "RHEA1022:21"}, {"id": "RHEA1022:22"}]}
        epilog.append(pformat(example))

        epilog.append(_("By Date Range"))
        example_date = {"date_range":{"start": "2013-04-15", "end": "2015-04-15"}}
        epilog.append(pformat(example_date))
        epilog.append(_("By Errata Type"))
        example = {"errata_type":["security", "bugfix"]}
        epilog.append(pformat(example))
        epilog.append(_("By Date Range and Errata Type"))
        example.update(example_date)
        epilog.append(pformat(example))
        epilog.append("")

        epilog.append(_("Puppet Module") + ": (puppet_module)")
        epilog.append(_("Specification"))
        epilog.append("""{"units":<["name", "author", "version", "min_version", "max_version"]*>}""")
        example = {"units": [{"name": "m*", "author": "puppetlabs", "version": "2.0.7"},
                  {"name": "httpd", "min_version": "2.0.4", "max_version": "2.0.8"}]}
        epilog.append(_("Examples"))
        epilog.append(pformat(example))
        epilog.append("")

        return "\n".join(epilog)


class RemoveRule(FilterAction):

    @property
    def description(self):
        return _('remove a rule from a filter')

    def __init__(self):
        super(RemoveRule, self).__init__()

    def setup_parser(self, parser):
        opt_parser_add_org(parser, required=1)
        parser.add_option('--rule_id', dest='rule',
                          help=_("id of the rule (required)"))
        self._add_get_filter_opts(parser)

    def check_options(self, validator):
        validator.require(('rule', 'org'))
        self._add_filter_opts_check(validator)
        self._add_cvd_opts_check(validator)

    def run(self):
        org_name = self.get_option('org')
        filter_name = self.get_option('name')
        filter_id = self.get_option('id')
        rule = self.get_option('rule')
        definition_label = self.get_option('definition_label')
        definition_name = self.get_option('definition_name')
        definition_id = self.get_option('definition_id')

        definition = get_cv_definition(org_name, definition_label,
                                       definition_name, definition_id)
        cvd_filter = get_filter(org_name, definition["id"], filter_name, filter_id)
        self.api.remove_rule(cvd_filter["id"], definition["id"], org_name, rule)

        print _("Successfully removed rule [ %s ]") % rule
        return os.EX_OK

class Filter(Command):

    description = _('content view definition filters actions for the katello server')
