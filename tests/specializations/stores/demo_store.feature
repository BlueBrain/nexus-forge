#  Scenario: A resource contains the last modifying action performed on it.
#    Given I create a resource with a property.
#    When The resource is validated.
#    Then The result of the vali
#
#  Scenario: Synchronization status is updated automatically at modification.
#    Given I create a resource with a property.
#    When The resource is synchronized.
#    And I modify the resource.
#    Then The synchronization status should be updated to False.