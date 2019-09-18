from functools import wraps


def catch(fun):
    # POLICY Should wrap operations dealing with resources but not modifying them.
    @wraps(fun)
    def wrapper(*args):
        try:
            return fun(*args)
        except Exception as e:
            print(f"<error> {e}"
                  f"\n<action> {fun.__name__}"
                  f"\n<args> {args}")
            return None
    return wrapper
