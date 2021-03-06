import sys

import pytest

import pylint_protobuf
from conftest import CheckerTestCase, extract_node, make_message


@pytest.fixture
def enum_mod(proto_builder):
    return proto_builder("""
        syntax = "proto2";
        package test;
        enum Variable {
          CONTINUOUS = 0;
          DISCRETE = 1;
        }
    """, 'enum')


@pytest.fixture
def nested_enum_mod(proto_builder):
    return proto_builder("""
        syntax = "proto2";
        package test;

        enum Outer {
          UNDEFINED = 0;
          ONE = 1;
          TWO = 2;
        }

        message Message {
          enum Inner {
            UNDEFINED = 0;
            UNO = 1;
            DOS = 2;
          }
        }
    """, 'nested_enum')


@pytest.fixture
def package_nested_enum_mod(proto_builder):
    return proto_builder("""
        syntax = "proto2";
        package test;

        enum Outer {
          UNDEFINED = 0;
          ONE = 1;
          TWO = 2;
        }

        message Message {
          enum Inner {
            UNDEFINED = 0;
            UNO = 1;
            DOS = 2;
          }
        }
    """, 'package.nested_enum')


class TestEnumDefinitions(CheckerTestCase):
    CHECKER_CLASS = pylint_protobuf.ProtobufDescriptorChecker

    def test_import_enum_types_no_errors(self, enum_mod):
        self.assert_no_messages(extract_node("""
            from {} import Variable
            print(Variable)
        """.format(enum_mod)))

    def test_import_enum_values_no_errors(self, enum_mod):
        self.assert_no_messages(extract_node("""
            from {} import DISCRETE
            print(DISCRETE)
        """.format(enum_mod)))

    def test_import_enum_attributes_no_errors(self, enum_mod):
        self.assert_no_messages(extract_node("""
            from {} import Variable
            print(Variable.DISCRETE)
        """.format(enum_mod)))

    def test_import_enum_missing_attributes_warns(self, enum_mod):
        node = extract_node("""
            from {} import Variable
            print(
                Variable.should_warn  #@
            )
        """.format(enum_mod))
        msg = make_message(node, enum_mod+'.Variable', 'should_warn')
        self.assert_adds_messages(node, msg)

    def test_import_enum_by_value_no_errors(self, enum_mod):
        self.assert_no_messages(extract_node("""
            from {} import Variable
            print(Variable.Value('DISCRETE'))
        """.format(enum_mod)))

    def test_star_import_enum_no_errors(self, enum_mod):
        self.assert_no_messages(extract_node("""
            from {} import *
            print(DISCRETE)
        """.format(enum_mod)))

    def test_star_import_enum_should_warn(self, enum_mod):
        node = extract_node("""
            from {} import *
            Variable.should_warn  #@
        """.format(enum_mod))
        msg = make_message(node, enum_mod+'.Variable', 'should_warn')
        self.assert_adds_messages(node, msg)

    @pytest.mark.xfail(reason='unimplemented')
    def test_import_enum_missing_attribute_by_value_warns(self, enum_mod):
        node = extract_node("""
        from {} import Variable
        print(
            Variable.Value('should_warn')  #@
        )
        """.format(enum_mod))
        msg = make_message(node, enum_mod+'.Variable', 'should_warn')
        self.assert_adds_messages(node, msg)

    def test_issue16_toplevel_enum(self, nested_enum_mod):
        self.assert_no_messages(extract_node("""
            import {mod}
            {mod}.ONE
        """.format(mod=nested_enum_mod)))

    def test_issue16_nested_enum_definition_direct_reference_no_errors(self, nested_enum_mod):
        self.assert_no_messages(extract_node("""
            import {mod} as sut
            {mod}.Message.Inner.UNO
        """.format(mod=nested_enum_mod)))

    @pytest.mark.xfail(reason='nested namespaces unimplemented')
    def test_issue16_nested_enum_definition_no_errors(self, nested_enum_mod):
        self.assert_no_messages(extract_node("""
            import {mod}
            {mod}.Message.UNO
        """.format(mod=nested_enum_mod)))

    @pytest.mark.xfail(reason='nested namespaces unimplemented')
    def test_fixme_issue16_nested_enum_definition_no_errors(self, nested_enum_mod):
        self.assert_no_messages(extract_node("""
            import {} as sut
            sut.Message.UNO
        """.format(nested_enum_mod)))

    @pytest.mark.xfail(reason='nested namespaces unimplemented')
    def test_issue16_package_nested_enum_definition_warns(self, pacage_nested_enum_mod):
        node = extract_node("""
            import {mod}
            {mod}.Message.should_warn
        """.format(mod=nested_enum_mod))
        msg = make_message(node, nested_enum_mod+'.Message', 'should_warn')
        self.assert_adds_messages(node, msg)

    def test_issue16_nested_enum_definition_warns(self, nested_enum_mod):
        node = extract_node("""
            import {} as sut
            sut.Message.should_warn
        """.format(nested_enum_mod))
        msg = make_message(node, nested_enum_mod+'.Message', 'should_warn')
        self.assert_adds_messages(node, msg)

    def test_issue16_missing_toplevel_enum(self, nested_enum_mod):
        node = extract_node("""
            import {} as sut
            sut.UNO
        """.format(nested_enum_mod))
        msg = make_message(node, nested_enum_mod, 'UNO')
        self.assert_adds_messages(node, msg)

    @pytest.mark.xfail(reason='nested namespaces unimplemented')
    def test_issue16_package_missing_toplevel_enum(self, package_nested_enum_mod):
        node = extract_node("""
            import {mod}
            {mod}.UNO
        """.format(mod=nested_enum_mod))
        msg = make_message(node, nested_enum_mod, 'UNO')
        self.assert_adds_messages(node, msg)

    @pytest.mark.skipif(sys.version_info < (3, 0),
                        reason='function annotations are Python 3+')
    def test_issue21_nested_enum_annassign(self, nested_enum_mod):
        self.assert_no_messages(extract_node("""
            import {} as sut
            def fun(type_: sut.Message.Inner):
                pass
        """.format(nested_enum_mod)))

    @pytest.mark.xfail(reason='issue #21 unfixed')
    def test_issue21_missing_field_on_nested_enum(self, nested_enum_mod):
        node = extract_node("""
            import {} as sut
            sut.Message.Inner.NOPE = 123
        """.format(nested_enum_mod))
        msg = make_message(node.targets[0], nested_enum_mod+'.Message.Inner', 'NOPE')
        self.assert_adds_messages(node, msg)
