#! /bin/sh

### BEGIN INIT INFO
# Provides:          MitsiTTP.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
### END INIT INFO

# If you want a command to always run, put it here

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting Mitsi HTTP"
    {{splitpipath}}/MitsiTTP.py &
    ;;
  stop)
    echo "Stopping Mitsi HTTP"
    pkill -f {{splitpipath}}/MitsiTTP.py
    ;;
  *)
    echo "Usage: /etc/init.d/mitsittp.sh {start|stop}"
    exit 1
    ;;
esac

exit 0
