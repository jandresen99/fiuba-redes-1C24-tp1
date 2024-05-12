
local proto_rdt = Proto("redestp1", "Custom")


local command = ProtoField.string("redestp1.command", "Type")
local flags = ProtoField.string("redestp1.flags", "Flags")
local data_length = ProtoField.uint32("redestp1.data_length", "Data Length")
local seq_number = ProtoField.uint32("redestp1.seq_number", "Sequence Number")
local ack_number = ProtoField.uint32("redestp1.ack_number", "Acknowledgment Number")
local data = ProtoField.bytes("redestp1.data", "Data")


proto_rdt.fields = {command, flags, data_length, seq_number, ack_number, data}


function proto_rdt.dissector(buf, pinfo, tree)
    local subtree = tree:add(proto_rdt, buf())


    subtree:add(data_length, buf(2, 4))
    subtree:add(seq_number, buf(6, 4))
    subtree:add(ack_number, buf(10, 4))
    subtree:add(data, buf(414))

    if buf(0, 1):uint() == 1 then
        subtree:add(command, "UPLOAD_TYPE")
    end

    if buf(0, 1):uint() == 2 then
        subtree:add(command, "DOWNLOAD_TYPE")
    end
    
    if buf(1, 1):uint() == 0 then
        subtree:add(flags, "NO_FLAG")
    end
    
    if buf(1, 1):uint() == 1 then
        subtree:add(flags, "SYN")
    end

    if buf(1, 1):uint() == 2 then
        subtree:add(flags, "START_TRANSFER")
    end

    if buf(1, 1):uint() == 3 then
        subtree:add(flags, "FIN")
    end

    if buf(1, 1):uint() == 4 then
        subtree:add(flags, "ACK")
    end

    if buf(1, 1):uint() == 5 then
        subtree:add(flags, "SYNACK")
    end

    if buf(1, 1):uint() == 6 then
        subtree:add(flags, "DUPLICATE_ACK")
    end


    pinfo.cols.protocol:set("Custom")
end


local udp_port = DissectorTable.get("udp.port")
udp_port:add("0-65535", proto_rdt)

