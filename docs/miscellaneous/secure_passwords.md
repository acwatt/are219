From [this article](https://towardsdatascience.com/secure-password-handling-in-python-6b9f5747eca5)
in the Storing Securely section.

> Instead of storing passwords in an unprotected file, we can instead use 
system’s keyring, which is an application that can store secure credentials in 
> encrypted file in your home directory. This file by default uses your user 
> account login password for encryption, so it gets automatically unlocked when 
> you login and you therefore don’t have worry about extra password.

> To use keyring credentials in Python applications, we can use library called
`keyring`:

```python
# pip install keyring
import keyring
import keyring.util.platform_ as keyring_platform

print(keyring_platform.config_root())
# /home/username/.config/python_keyring  # Might be different for you

print(keyring.get_keyring())
# keyring.backends.SecretService.Keyring (priority: 5)

NAMESPACE = "my-app"
ENTRY = "API_KEY"

keyring.set_password(NAMESPACE, ENTRY, "a3491fb2-000f-4d9f-943e-127cfe29c39c")
print(keyring.get_password(NAMESPACE, ENTRY))
# a3491fb2-000f-4d9f-943e-127cfe29c39c

cred = keyring.get_credential(NAMESPACE, ENTRY)
print(f"Password for username {cred.username} in namespace {NAMESPACE} is {cred.password}")
# Password for username API_KEY in namespace my-app is a3491fb2-000f-4d9f-943e-127cfe29c39c
```

> In the above code, we start by checking location of keyring config file, which
is the place where you can make some configuration adjustments if needed. We
then check the active keyring and proceed with adding a password into it. Each
entry has 3 attributes — `service`, `username` and `password`, where `service`
acts as a namespace, which in this case would be a name of an application. To
create and retrieve an entry, we can just use `set_password()`
and `get_password()`
respectively. In addition to that, also `get_credential()` can be used - it
returns a credential object which has an attribute for `username` and `password`
.

In `acwatt_syp_code/utils/config.py`, we call `get_credentials()` for the
namespace `"aws_purpleair_downloader"` to get the  `access_key` and `secret_key`
associated with the AWS IAM role for this project. So to get this
code to 
run on another
computer, we must set the  `access_key` and `secret_key` using the code 
below. This should be done manually when running the code for the first time 
on a new computer -- your access key and secret key SHOULD NOT be put 
anywhere in the code. 

```python
import keyring

namespace1 = "aws_purpleair_downloader"
keyring.set_password(namespace1, "access_key", "your IAM role access key here")
keyring.set_password(namespace1, "secret_key", "your IAM role secret key here")

namespace2 = "purpleair_api"
keyring.set_password(namespace1, "read_key", "your PurpleAir read key here")
# keyring.set_password(namespace1, "write_key", "your PurpleAir write key here")
# write key not used currently
```

I have built this into `config.py` so when the application first runs, it 
will ask for all the necessary keys and add them to your computer's local 
keyring. This should only happen the first time the code runs, and if you've 
correctly input the keys and your IAM role has been granted access to the 
lambda service as well as the S3 bucket, then it should be able to run 
forever more. If you enter the keys incorrectly or you need to change them, 
you can run the code above in a python console.
