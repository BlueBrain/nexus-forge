Feature: Resource
  A Python object offering an integration point between the different elements
  of the Knowledge Graph Forge

  Scenario: Create a resource.
    Given I create a resource with a property.
    Then I should be able to access properties as object attribute.

  Scenario: Create a resource with a nested resource.
    Given I create a resource with an other resource as property.
    Then I should be able to access the nested resource properties as JSONPath.

  Scenario: There is a collision with a reserved attribute.
    When I create a resource with a reserved attribute. Creation should fail.

  Scenario: Create and update a resource.
    Given I create a resource with a property.
    Then I assigned _synchronized to True so the resource should give _inner_sync equals True.

  Scenario: Create and update a nested resource.
    Given I create a resource with an other resource as property.
    Then I changed a nested property so the resource should give _synchronized equals False.
  
  Scenario: Create a resource with id and type.
    Given I create a resource with an id and type.
    Then I should be able to get its type and identifier.