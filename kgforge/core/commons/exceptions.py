from functools import wraps


def catch(fun):
    # POLICY Should wrap operations on resources not managed by actions.run().
    @wraps(fun)
    def wrapper(*args):
        try:
            return fun(*args)
        except Exception as e:
            print(f"<action> {fun.__name__}"
                  f"\n<error> {e}"
                  f"\n<args> {args}")
            return None
    return wrapper
