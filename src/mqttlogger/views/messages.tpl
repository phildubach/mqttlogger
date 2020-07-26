% rebase('base.tpl', title="MQTT Logger | Message View")
% import time
<div class="container">
    % for message in messages:
    <div class="row">
        <div class="column column-20">{{time.strftime("%x %X", time.localtime(message[0]))}}</div>
        <div class="column column-40">{{message[1]}}</div>
        <div class="column column-40">{{message[2]}}</div>
    </div>
    %end
</div>
