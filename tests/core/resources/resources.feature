Feature: Resources
  A Python object offering a special handling of list of resources.

  Scenario: Create a Resources object from a collection of resources.
    Given I create a Resources object from a collection of resources.
    Then I should be able to count the number of resources with len().
    And The Resource objects should be in the same order as inserted.

  Scenario: Create a Resources object from existing resources.
    Given I create a Resources object from existing resources.
    Then I should be able to count the number of resources with len().
    And The Resource objects should be in the same order as inserted.
