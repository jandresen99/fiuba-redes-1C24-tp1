
local proto_rdt = Proto("redestp1", "RDT GA6")


local command = ProtoField.uint8("redestp1.command", "Type")
local flags = ProtoField.uint8("redestp1.flags", "Flags")
local data_length = ProtoField.uint32("redestp1.data_length", "Data Length")
local seq_number = ProtoField.uint32("redestp1.seq_number", "Sequence Number")
local ack_number = ProtoField.uint32("redestp1.ack_number", "Acknowledgment Number")
local data = ProtoField.bytes("redestp1.data", "Data")


proto_rdt.fields = {command, flags, data_length, seq_number, ack_number, data}


function proto_rdt.dissector(buf, pinfo, tree)
    local subtree = tree:add(proto_rdt, buf())


    subtree:add(command, buf(0, 1))
    subtree:add(flags, buf(1, 1))
    subtree:add(data_length, buf(2, 4))
    subtree:add(seq_number, buf(6, 4))
    subtree:add(ack_number, buf(10, 4))
    subtree:add(data, buf(414))


    pinfo.cols.protocol:set("RDT GA6")
end


local udp_port = DissectorTable.get("udp.port")
udp_port:add(8080, proto_rdt)

