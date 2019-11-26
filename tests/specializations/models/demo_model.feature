Feature: Model
  An interface representing what a data model should and could provide to
  the user and the other elements of the Knowledge Graph Forge.

  Scenario: The validation of a resource succeeds.
    Given A model instance.
    And A valid resource.
    When I validate the resource. The printed report does not mention an error.
    Then The '_validated' status of the resource should be 'True'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_validate_one'.
    And The report should say that the operation success is 'True'.
    And The report should say that the error was 'None'.

  Scenario: The validation of resources succeeds.
    Given A model instance.
    And Valid resources.
    When I validate the resources. The printed report does not mention an error.
    Then The '_validated' status of a resource should be 'True'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_validate_one'.
    And The report should say that the operation success is 'True'.
    And The report should say that the error was 'None'.

  Scenario: The validation of a resource fails.
    Given A model instance.
    And An invalid resource.
    When I validate the resource. The printed report does mention an error: 'ValidationError: name is missing'.
    Then The '_validated' status of the resource should be 'False'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_validate_one'.
    And The report should say that the operation success is 'False'.
    And The report should say that the error was 'ValidationError'.

  Scenario: The validation of resources fails.
    Given A model instance.
    And Invalid resources.
    When I validate the resources. The printed report does mention an error: 'ValidationError: name is missing'.
    Then The '_validated' status of a resource should be 'False'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_validate_one'.
    And The report should say that the operation success is 'False'.
    And The report should say that the error was 'ValidationError'.

  Scenario: An exception is raised during the validation of a resource.
    Given A model instance.
    And A valid resource.
    When I validate the resource. An exception is raised. The printed report mentions an error: 'Exception: exception raised'.
    Then The '_validated' status of the resource should be 'False'.
    And I should be able to access the report of the action on a resource.
    And The report should say that the operation was '_validate_one'.
    And The report should say that the operation success is 'False'.
    And The report should say that the error was 'Exception'.

  Scenario: Modifying a validated resource sets its validation status to False.
    Given A validated resource.
    When I modify the resource.
    Then The '_validated' status of the resource should be 'False'.
