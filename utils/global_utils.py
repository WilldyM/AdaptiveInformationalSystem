import bcrypt
from fastnumbers import fast_real


def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)


def dict_inner_rename_value(dct: dict, value, *recurring_keys, pattern: tuple = None) -> dict:
    eval_str__if = 'dct'
    exec_str__set = 'dct'
    eval_str__pattern = ''
    enumerating_patterns = {0: ''}
    for i, reccuring_key in enumerate(recurring_keys):
        if isinstance(fast_real(reccuring_key), str):
            eval_str__if += f'.get(\'{reccuring_key}\', {"{}"})'
            eval_str__pattern += f'.get(\'{reccuring_key}\', {"{}"})'
            exec_str__set += f'[\'{reccuring_key}\']'
            enumerating_patterns[i+1] = eval_str__pattern
        else:
            eval_str__if += f'.get({reccuring_key}, {"{}"})'
            exec_str__set += f'[{reccuring_key}]'
            enumerating_patterns[i+1] = eval_str__if
    exec_str__set += ' = value'
    try:
        if eval(eval_str__if) != {}:
            if pattern:
                main_pttrn_eval_str = 'dct'+enumerating_patterns.get(pattern[0]-1)
                eval_patterns = []
                for k, v in pattern[1].items():
                    eval_patterns.append(f'{main_pttrn_eval_str}.get(k, None) == v')

                for eval_pattern in eval_patterns:
                    if eval(eval_pattern):
                        continue
                    else:
                        raise AttributeError()
            exec(exec_str__set)
    except AttributeError:
        pass
    for k, v in dct.items():
        if isinstance(v, dict):
            dct[k] = dict_inner_rename_value(v, value, *recurring_keys, pattern=pattern)
    return dct


def dict_inner_rename_key(dct: dict, old_key, new_key, inner_pattern=None) -> dict:
    try:
        if old_key in dct.keys():
            if inner_pattern:
                for k, v in inner_pattern.items():
                    if dct[old_key].get(k) != v:
                        raise AttributeError()
            dct[new_key] = dct.pop(old_key)
    except AttributeError:
        pass
    for k, v in dct.items():
        if isinstance(v, dict):
            dct[k] = dict_inner_rename_key(v, old_key, new_key)
    return dct