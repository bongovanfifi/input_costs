
**The security features are garbage. Don't rely on them!** I tried to go at least a little further than the basic approach shown [here](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso) to make the password harder to brute force, but you could just [use a managed service](https://docs.streamlit.io/develop/concepts/connections/authentication) or this you could [use streamlit-authenticator](https://blog.streamlit.io/streamlit-authenticator-part-1-adding-an-authentication-component-to-your-app/), which seems pretty cool.

**Streamlit will dumb the sqlite db on every reboot!** If you really wanted to, you could just manually stick the backed up db back into the environment with the code editor, but that's a very janky way to get persistence.

This could be made a lot more stable by constantly communicating with some remote RDBMS rather than just using sqlite and backing it up manually in admin. I did it this way because I wanted a tool that was fast, responsive, could be created in one day, and cost nothing. Technically, backing up to s3 costs some fraction of a penny, but I'm happy calling that "nothing". If you're already paying for a lot more infrastructure, you should probably use that instead. Pointing this to a remote DB should be very easy, I've provided the table schemas and everything.

Your secrets.toml should look like this:

```
[connections.db]
url = "foo"

[passwords]
admin = "foo"
kitchen = "foo"


[aws]
access_key_id = "foo"
secret_access_key = "foo"
bucket_name = "foo"
region = "foo"
``` 

Obviously, you also have to set up an IAM role with PutObject permissions for wherever you are putting the backup.

With this app, I'm continuing my habit of dedicating a full day to going from nothing to an MVP. In this case there was way more work than I thought. In hindisght, maybe I should have made this a normal React app. I had not used Streamlit but I assumed it would help much more than it did.