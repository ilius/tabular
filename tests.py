#!/usr/bin/env python3
import unittest
import tabular


class TestParser(unittest.TestCase):
    def check_equality(self, inp, exp, extraskip=0):
        self.maxDiff = None
        lines = inp.split("\n")
        # first line is blank because of formatting
        res = tabular.parse_lines(lines[1+extraskip:])
        res_as_dict = [dict(x) for x in res]
        return self.assertEqual(res_as_dict, exp)

    def test_basic(self):
        inp = """
One     Two    Three
1.1     1.2    1.3
2.1     2.2    2.3
"""
        exp = [
            {"One": "1.1", "Two": "1.2", "Three": "1.3"},
            {"One": "2.1", "Two": "2.2", "Three": "2.3"}
        ]
        self.check_equality(inp, exp)

    def test_docker(self):
        inp = """
CONTAINER ID        IMAGE                      COMMAND                  CREATED             STATUS              PORTS                                                                       NAMES
a5b04a56f27c        docker_dashboard           "npm start"              3 days ago          Up 18 minutes       127.0.0.1:4000->4000/tcp, 5858/tcp                                          docker_dashboard_1
7755ce972c33        docker_crawler             "docker-entrypoint.s…"   3 days ago          Up 18 minutes       0.0.0.0:3000->3000/tcp, 5858/tcp                                            docker_crawler_1
f41dca732dbe        metabase/metabase:latest   "/app/run_metabase.sh"   3 days ago          Up 18 minutes       127.0.0.1:5000->3000/tcp                                                    docker_metabase_1
3808427a882c        rabbitmq:management        "docker-entrypoint.s…"   3 days ago          Up 18 minutes       4369/tcp, 5671-5672/tcp, 15671/tcp, 25672/tcp, 127.0.0.1:15672->15672/tcp   docker_rabbitmq_1
9d62a5cef692        mongo:latest               "docker-entrypoint.s…"   3 days ago          Up 18 minutes       127.0.0.1:27017->27017/tcp                                                  docker_mongo_1
624d7758cbe3        redis:latest               "docker-entrypoint.s…"   3 days ago          Up 18 minutes       127.0.0.1:6379->6379/tcp                                                    docker_redis_1
"""
        exp = [
            {
                "CONTAINER ID": "a5b04a56f27c",
                "IMAGE": "docker_dashboard",
                "COMMAND": "\"npm start\"",
                "CREATED": "3 days ago",
                "STATUS": "Up 18 minutes",
                "PORTS": "127.0.0.1:4000->4000/tcp, 5858/tcp",
                "NAMES": "docker_dashboard_1"
            },
            {
                "CONTAINER ID": "7755ce972c33",
                "IMAGE": "docker_crawler",
                "COMMAND": "\"docker-entrypoint.s\u2026\"",
                "CREATED": "3 days ago",
                "STATUS": "Up 18 minutes",
                "PORTS": "0.0.0.0:3000->3000/tcp, 5858/tcp",
                "NAMES": "docker_crawler_1"
            },
            {
                "CONTAINER ID": "f41dca732dbe",
                "IMAGE": "metabase/metabase:latest",
                "COMMAND": "\"/app/run_metabase.sh\"",
                "CREATED": "3 days ago",
                "STATUS": "Up 18 minutes",
                "PORTS": "127.0.0.1:5000->3000/tcp",
                "NAMES": "docker_metabase_1"
            },
            {
                "CONTAINER ID": "3808427a882c",
                "IMAGE": "rabbitmq:management",
                "COMMAND": "\"docker-entrypoint.s\u2026\"",
                "CREATED": "3 days ago",
                "STATUS": "Up 18 minutes",
                "PORTS": "4369/tcp, 5671-5672/tcp, 15671/tcp, 25672/tcp, 127.0.0.1:15672->15672/tcp",
                "NAMES": "docker_rabbitmq_1"
            },
            {
                "CONTAINER ID": "9d62a5cef692",
                "IMAGE": "mongo:latest",
                "COMMAND": "\"docker-entrypoint.s\u2026\"",
                "CREATED": "3 days ago",
                "STATUS": "Up 18 minutes",
                "PORTS": "127.0.0.1:27017->27017/tcp",
                "NAMES": "docker_mongo_1"
            },
            {
                "CONTAINER ID": "624d7758cbe3",
                "IMAGE": "redis:latest",
                "COMMAND": "\"docker-entrypoint.s\u2026\"",
                "CREATED": "3 days ago",
                "STATUS": "Up 18 minutes",
                "PORTS": "127.0.0.1:6379->6379/tcp",
                "NAMES": "docker_redis_1"
            }
        ]
        self.check_equality(inp, exp)

    @unittest.skip
    def test_ps(self):
        """Note: this test is known to fail. The problem is that there's nothing
        obvious showing where the dividing line between TTY and TIME is. So they
        get lumped into one column. This needs fixing."""
        inp = """
  PID TTY          TIME CMD
 4960 pts/9    00:00:01 bash
 4970 pts/9    00:00:00 ps
"""
        exp = [
            {"PID": "4960", "TTY": "pts/9", "TIME": "00:00:01", "CMD": "bash"},
            {"PID": "4967", "TTY": "pts/9", "TIME": "00:00:00", "CMD": "ps"}
        ]
        self.check_equality(inp, exp)

    def test_netstat(self):
        inp = """
Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 127.0.0.1:4000          0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:17600         0.0.0.0:*               LISTEN      9244/dropbox        
tcp        0      0 127.0.0.1:17603         0.0.0.0:*               LISTEN      9244/dropbox        
tcp        0      0 0.0.0.0:902             0.0.0.0:*               LISTEN      -                   
"""
        exp = [
            {
                "Proto": "tcp",
                "Recv-Q": "0",
                "Send-Q": "0",
                "Local Address": "127.0.0.1:4000",
                "Foreign Address": "0.0.0.0:*",
                "State": "LISTEN",
                "PID/Program name": "-"
            },
            {
                "Proto": "tcp",
                "Recv-Q": "0",
                "Send-Q": "0",
                "Local Address": "127.0.0.1:17600",
                "Foreign Address": "0.0.0.0:*",
                "State": "LISTEN",
                "PID/Program name": "9244/dropbox"
            },
            {
                "Proto": "tcp",
                "Recv-Q": "0",
                "Send-Q": "0",
                "Local Address": "127.0.0.1:17603",
                "Foreign Address": "0.0.0.0:*",
                "State": "LISTEN",
                "PID/Program name": "9244/dropbox"
            },
            {
                "Proto": "tcp",
                "Recv-Q": "0",
                "Send-Q": "0",
                "Local Address": "0.0.0.0:902",
                "Foreign Address": "0.0.0.0:*",
                "State": "LISTEN",
                "PID/Program name": "-"
            }
        ]
        self.check_equality(inp, exp, extraskip=1)


if __name__ == "__main__":
    unittest.main()
