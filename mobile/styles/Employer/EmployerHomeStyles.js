import { StyleSheet } from "react-native";

export default StyleSheet.create({
    container: { flex: 1, backgroundColor: '#FAFAFD', paddingHorizontal: 20, paddingTop: 50 },

    // Header
    header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },

    // Search
    searchBar: {
        backgroundColor: 'white',
        borderRadius: 12,
        marginBottom: 25,
        elevation: 0, // Xóa bóng cho giống hình phẳng
        borderWidth: 1,
        borderColor: '#F0F0F0'
    },

    // Banner
    bannerContainer: {
        backgroundColor: '#3D5CFF', // Màu xanh dương đậm giống hình
        borderRadius: 20,
        height: 160,
        flexDirection: 'row',
        overflow: 'hidden',
        marginBottom: 30,
        padding: 20,
        position: 'relative'
    },
    bannerContent: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    bannerTitle: { color: 'white', fontSize: 20, fontWeight: 'bold', marginBottom: 15, lineHeight: 28 },

    // Grid Stats
    sectionTitle: { fontWeight: 'bold', marginBottom: 15, fontSize: 18, color: '#0D0D26' },
    gridContainer: { flexDirection: 'row', justifyContent: 'space-between', height: 170, marginBottom: 30 },

    cardLeft: {
        width: '48%', height: '100%',
        borderRadius: 16, padding: 20,
        justifyContent: 'center', alignItems: 'center'
    },
    colRight: { width: '48%', justifyContent: 'space-between' },
    cardRight: {
        width: '100%', height: '100%',
        borderRadius: 16,
        justifyContent: 'center', alignItems: 'center'
    },

    iconCircle: { width: 45, height: 45, borderRadius: 22.5, justifyContent: 'center', alignItems: 'center', marginBottom: 10 },
    statNumber: { fontSize: 26, fontWeight: 'bold', color: '#0D0D26' },
    statNumberSmall: { fontSize: 20, fontWeight: 'bold', color: '#0D0D26' },
    statLabel: { fontSize: 14, color: '#0D0D26', opacity: 0.7, marginTop: 2 },

    // Job List Card (Recent Applicants)
    jobCard: {
        backgroundColor: 'white',
        borderRadius: 16,
        marginBottom: 15,
        elevation: 0, // Flat style
        shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.05, shadowRadius: 10
    },
    logoBox: { width: 45, height: 45, borderRadius: 10, backgroundColor: '#F5F6FA', justifyContent: 'center', alignItems: 'center' },
    tag: { backgroundColor: '#F5F6FA', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, marginRight: 8 },
    tagText: { color: '#95969D', fontSize: 11 },
    fab: {
        position: 'absolute',
        margin: 16,
        right: 0,
        bottom: 0,
        backgroundColor: '#3D5CFF', // Màu xanh dương đậm của Banner
        borderRadius: 50, // Bo tròn hoàn hảo
        elevation: 4, // Đổ bóng nhẹ
        zIndex: 10, // Đảm bảo nổi lên trên cùng
    },
});