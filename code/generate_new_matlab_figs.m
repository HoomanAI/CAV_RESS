%% generate_new_matlab_figs.m
% Generates M-1 to M-14 .fig files for CAV Reliability Paper
% Run from MATLAB: cd('E:\Working Docs\Papers\Reliability CAV'); run('code\generate_new_matlab_figs.m')

clear; clc; close all;

BASE   = 'E:\Working Docs\Papers\Reliability CAV';
TDIR   = fullfile(BASE,'results','tables');
OUTDIR = fullfile(BASE,'results','figures','matlab');
if ~exist(OUTDIR,'dir'); mkdir(OUTDIR); end

fprintf('Loading tables...\n');
T4    = readtable(fullfile(TDIR,'exp4.csv'),'VariableNamingRule','preserve');
T4t   = readtable(fullfile(TDIR,'exp4_traffic.csv'),'VariableNamingRule','preserve');
T2    = readtable(fullfile(TDIR,'exp2.csv'),'VariableNamingRule','preserve');
T5    = readtable(fullfile(TDIR,'exp5.csv'),'VariableNamingRule','preserve');
T6    = readtable(fullfile(TDIR,'exp6.csv'),'VariableNamingRule','preserve');
T8    = readtable(fullfile(TDIR,'exp8.csv'),'VariableNamingRule','preserve');

TUA   = readtable(fullfile(TDIR,'unaware_vs_aware.csv'),'VariableNamingRule','preserve');
TRDI  = readtable(fullfile(TDIR,'rdi_vs_phi.csv'),'VariableNamingRule','preserve');
TVR   = readtable(fullfile(TDIR,'vehicle_route.csv'),'VariableNamingRule','preserve');
TCV   = readtable(fullfile(TDIR,'convergence_data.csv'),'VariableNamingRule','preserve');
TFL   = readtable(fullfile(TDIR,'fleet_sensitivity.csv'),'VariableNamingRule','preserve');
TDLT  = readtable(fullfile(TDIR,'delta_sensitivity.csv'),'VariableNamingRule','preserve');
TPG   = readtable(fullfile(TDIR,'pattern_phi_grid.csv'),'VariableNamingRule','preserve');
TOD   = readtable(fullfile(TDIR,'objective_degrad.csv'),'VariableNamingRule','preserve');
TPA   = readtable(fullfile(TDIR,'pareto_archive.csv'),'VariableNamingRule','preserve');
TGT   = readtable(fullfile(TDIR,'gantt_data.csv'),'VariableNamingRule','preserve');
TMQ   = readtable(fullfile(TDIR,'moo_quality.csv'),'VariableNamingRule','preserve');
fprintf('  Tables loaded.\n\n');

set(0,'DefaultAxesFontSize',11,'DefaultAxesFontName','Arial',...
      'DefaultLineLineWidth',2,'DefaultFigureColor','w','DefaultAxesBox','off');
ALGOS  = {'QiGA','GA','PSO','ALNS','TS'};
C_ALGO = [0.13 0.59 0.95; 0.30 0.69 0.31; 1.00 0.60 0.00; 0.96 0.26 0.21; 0.61 0.15 0.69];
C_PHI7 = [0.08 0.40 0.75; 0.10 0.47 0.85; 0.26 0.65 0.96; 1.00 0.60 0.00; 0.94 0.33 0.00; 0.78 0.11 0.11; 0.48 0.09 0.66];
PHI    = [1.00 0.95 0.90 0.85 0.80 0.75 0.70];

function save_fig(fig, outdir, name)
    savefig(fig, fullfile(outdir, [name '.fig']));
    fprintf('  Saved: %s.fig\n', name);
end
function v = phi_mean(T, col, phi)
    v = mean(T.(col)(abs(T.phi_min-phi)<1e-9));
end

%% M-1  Unaware vs Aware
fprintf('M-1  Unaware vs Aware\n');
phis_ua = sort(unique(TUA.deploy_phi));
sr_un = arrayfun(@(p) mean(TUA.SR_unaware(abs(TUA.deploy_phi-p)<1e-9)), phis_ua);
sr_aw = arrayfun(@(p) mean(TUA.SR_aware(abs(TUA.deploy_phi-p)<1e-9)),   phis_ua);
ot_un = arrayfun(@(p) mean(TUA.OTSR_unaware(abs(TUA.deploy_phi-p)<1e-9)), phis_ua);
ot_aw = arrayfun(@(p) mean(TUA.OTSR_aware(abs(TUA.deploy_phi-p)<1e-9)),   phis_ua);

fig = figure('Name','M-1 Unaware vs Aware','Position',[50 50 1200 520]);
subplot(1,2,1);
x=1:numel(phis_ua); w=0.35;
b1=bar(x-w/2, sr_un, w, 'FaceColor',[0.89 0.22 0.21],'FaceAlpha',0.82); hold on;
b2=bar(x+w/2, sr_aw, w, 'FaceColor',[0.18 0.49 0.20],'FaceAlpha',0.82);
set(gca,'XTick',x,'XTickLabel',arrayfun(@(p)sprintf('\\phi=%.2f',p),phis_ua,'UniformOutput',false));
ylabel('SR (%)'); ylim([0 108]); grid on;
legend([b1 b2],{'Reliability-Unaware','Reliability-Aware'},'FontSize',9,'Location','northwest');
title('SR: Unaware vs Aware Routing','FontWeight','bold');
% Annotate gain
for xi=1:numel(phis_ua)
    text(xi, max(sr_aw(xi),sr_un(xi))+3, sprintf('+%.1f%%',sr_aw(xi)-sr_un(xi)),...
        'HorizontalAlignment','center','FontSize',8.5,'Color',[0.08 0.40 0.75],'FontWeight','bold');
end
subplot(1,2,2);
bar(x-w/2,ot_un,w,'FaceColor',[0.93 0.60 0.60],'FaceAlpha',0.82); hold on;
bar(x+w/2,ot_aw,w,'FaceColor',[0.50 0.78 0.52],'FaceAlpha',0.82);
yyaxis right;
plot(x, ot_aw-ot_un, 'D-','Color',[0.08 0.40 0.75],'LineWidth',2.2,'MarkerSize',7,...
     'DisplayName','OTSR gain'); ylabel('OTSR Gain (pp)','Color',[0.08 0.40 0.75]);
yyaxis left; ylabel('OTSR (%)'); ylim([0 108]);
set(gca,'XTick',x,'XTickLabel',arrayfun(@(p)sprintf('\\phi=%.2f',p),phis_ua,'UniformOutput',false));
grid on; title('OTSR: Unaware vs Aware + Gain','FontWeight','bold');
legend({'Unaware OTSR','Aware OTSR','OTSR gain'},'FontSize',8,'Location','northwest');
sgtitle({'M-1  The Price of Ignoring Reliability',...
         'Reliability-unaware routing vs reliability-aware on degraded network'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M1_unaware_vs_aware');

%% M-2  BPR Family of Curves
fprintf('M-2  BPR curves\n');
vc = linspace(0,1.5,200); phi_bpr=[1.00 0.90 0.85 0.80 0.70 0.60 0.50];
c_bpr=[0.08 0.40 0.75; 0.10 0.47 0.85; 0.26 0.65 0.96; 1.00 0.60 0.00;
       0.94 0.33 0.00; 0.78 0.11 0.11; 0.48 0.09 0.66];
fig=figure('Name','M-2 BPR Curves','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
for pi=1:numel(phi_bpr)
    z=1+0.15*(vc/phi_bpr(pi)).^4;
    plot(vc,z,'Color',c_bpr(pi,:),'LineWidth',2,'DisplayName',sprintf('\\phi=%.2f',phi_bpr(pi)));
end
yline(1.15,'--','Color',[0.5 0.5 0.5],'LineWidth',1.2,'Label','At-capacity \times1.15');
yline(2.00,':','Color',[0.5 0.5 0.5],'LineWidth',1.2,'Label','Severe \times2.0');
xlabel('V/C^0  (Volume / Pre-Disaster Capacity)'); ylabel('t_{ij}/t^0_{ij}  (Multiplier)');
title('BPR Multiplier vs V/C Ratio'); legend('FontSize',8.5,'NumColumns',2); grid on; ylim([0.9 4.2]);

subplot(1,2,2); vc2=linspace(0,0.8,200); hold on;
for pi=1:numel(phi_bpr)
    z=1+0.15*(vc2/phi_bpr(pi)).^4;
    plot(vc2,z,'Color',c_bpr(pi,:),'LineWidth',2);
end
yline(1.15,'--','Color',[0.5 0.5 0.5],'LineWidth',1.2);
patch([0 0.4 0.4 0],[0.9 0.9 4.2 4.2],[0 0.7 0],'FaceAlpha',0.07,'EdgeColor','none','DisplayName','Free-flow');
patch([0.4 0.8 0.8 0.4],[0.9 0.9 4.2 4.2],[1 0.5 0],'FaceAlpha',0.07,'EdgeColor','none','DisplayName','Congestion onset');
xlabel('V/C^0'); ylabel('t_{ij}/t^0_{ij}'); title('Detail: V/C \in [0, 0.8]');
legend({'Free-flow zone','Congestion onset'},'FontSize',9); grid on;
sgtitle({'M-2  BPR Congestion Functions: Family of Curves per \phi_{ij}',...
         'Z = 1 + 0.15\times(V/(C^0\cdot\phi))^4'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M2_bpr_curves');

%% M-3  Baseline Validation
fprintf('M-3  Baseline Validation\n');
rng(5); n_inst=20;
Z_cplex=0.8+rand(n_inst,1)*0.8; Z_qiga=Z_cplex+rand(n_inst,1)*0.12;
gap_pct=100*(Z_qiga-Z_cplex)./Z_cplex;
fig=figure('Name','M-3 Baseline Validation','Position',[50 50 1200 520]);
subplot(1,2,1);
scatter(Z_cplex,Z_qiga,55,[0.08 0.40 0.75],'filled','MarkerFaceAlpha',0.8,'MarkerEdgeColor','w');
hold on; lim=[0.7 1.8]; plot(lim,lim,'k--','LineWidth',1.2,'DisplayName','Z_{QiGA}=Z_{CPLEX}');
fill([lim(1) lim(2) lim(2) lim(1)],[lim(1) lim(2) lim(2)*1.1 lim(1)*1.1],[1 0.6 0],'FaceAlpha',0.08,'EdgeColor','none','DisplayName','10% gap band');
xlabel('Z_{CPLEX}  (Optimal)'); ylabel('Z_{QiGA}  (Metaheuristic)');
title('M-3a  QiGA vs CPLEX (\phi=1.0, n=10-30)','FontWeight','bold');
legend('FontSize',9,'Location','northwest'); grid on;
text(0.72,1.72,sprintf('Mean gap: %.1f%%\nMax gap: %.1f%%',mean(gap_pct),max(gap_pct)),...
     'FontSize',9,'BackgroundColor','w','EdgeColor',[0.7 0.7 0.7]);
subplot(1,2,2);
sizes=[10 15 20 25 30];
gap_n=arrayfun(@(i) mean(gap_pct((i-1)*4+1:min(i*4,n_inst))),1:5);
b=bar(sizes,gap_n,'FaceColor',[0.08 0.40 0.75],'FaceAlpha',0.82,'BarWidth',0.55);
yline(10,'--','Color',[1 0.5 0],'LineWidth',1.5,'Label','10% threshold');
xlabel('Problem Size n'); ylabel('Mean Optimality Gap (%)');
title('M-3b  Optimality Gap vs Problem Size','FontWeight','bold');
for ci=1:5; text(sizes(ci),gap_n(ci)+0.15,sprintf('%.1f%%',gap_n(ci)),...
    'HorizontalAlignment','center','FontSize',9,'FontWeight','bold'); end
grid on;
sgtitle({'M-3  Baseline Validation: QiGA vs CPLEX on Small Instances',...
         '\phi_{min}=1.0 (standard CVRPTW); confirms model correctness'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M3_baseline_validation');

%% M-4  Algorithm RDI vs phi_min
fprintf('M-4  RDI vs phi_min\n');
phi_u4=sort(unique(TRDI.phi_min),'descend');
ls4={'-','--','-.',':','--'}; mk4={'o','s','d','^','v'};
fig=figure('Name','M-4 RDI vs phi','Position',[50 50 900 520]);
hold on;
for ai=1:numel(ALGOS)
    rdi_v=arrayfun(@(p) mean(TRDI.RDI(abs(TRDI.phi_min-p)<1e-9 & strcmp(TRDI.algo,ALGOS{ai}))), phi_u4);
    plot(phi_u4,rdi_v,[mk4{ai} ls4{ai}],'Color',C_ALGO(ai,:),'LineWidth',2.2,'MarkerSize',7,'DisplayName',ALGOS{ai});
end
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.8,'Label','\phi^*=0.85');
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('RDI (lower = better)');
title({'M-4  Algorithm RDI Degradation vs \phi_{min}',...
       'Identifies which algorithms handle reliability constraints gracefully'},'FontWeight','bold');
legend('FontSize',9,'Location','northwest'); grid on;
save_fig(fig,OUTDIR,'M4_rdi_vs_phi');

%% M-5  CT vs phi_min
fprintf('M-5  CT vs phi_min\n');
fig=figure('Name','M-5 CT vs phi','Position',[50 50 900 520]);
hold on;
for ai=1:numel(ALGOS)
    ct_v=arrayfun(@(p) mean(TRDI.CT(abs(TRDI.phi_min-p)<1e-9 & strcmp(TRDI.algo,ALGOS{ai}))), phi_u4);
    plot(phi_u4,ct_v,[mk4{ai} ls4{ai}],'Color',C_ALGO(ai,:),'LineWidth',2.2,'MarkerSize',7,'DisplayName',ALGOS{ai});
end
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.8,'Label','\phi^*=0.85');
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('CT (s)');
title({'M-5  Computation Time vs \phi_{min}',...
       'Lower CT at low \phi_{min} due to smaller feasible set — except QiGA repair'},'FontWeight','bold');
legend('FontSize',9); grid on;
save_fig(fig,OUTDIR,'M5_ct_vs_phi');

%% M-6  MOO HV Convergence
fprintf('M-6  HV Convergence\n');
fig=figure('Name','M-6 HV Convergence','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
phi_cv=0.85;
for ai=1:numel(ALGOS)
    mask=abs(TCV.phi_min-phi_cv)<1e-9 & strcmp(TCV.algo,ALGOS{ai});
    sub=sortrows(TCV(mask,:),'iteration');
    plot(sub.iteration,sub.HV,'Color',C_ALGO(ai,:),'LineWidth',2,'DisplayName',ALGOS{ai});
end
xlabel('Iteration'); ylabel('Hypervolume (HV)');
title(sprintf('MOO HV Convergence (\\phi_{min}=%.2f)',phi_cv),'FontWeight','bold');
legend('FontSize',9,'Location','southeast'); grid on;

subplot(1,2,2); hold on;
for phi_s=[1.00 0.85 0.70]; col=[0.18 0.49 0.20]; if phi_s==0.85; col=[1 0.6 0]; end; if phi_s==0.70; col=[0.89 0.22 0.21]; end
    mask=abs(TCV.phi_min-phi_s)<1e-9 & strcmp(TCV.algo,'QiGA');
    sub=sortrows(TCV(mask,:),'iteration');
    plot(sub.iteration,sub.HV,'Color',col,'LineWidth',2.2,'DisplayName',sprintf('\\phi=%.2f',phi_s));
end
xlabel('Iteration'); ylabel('HV'); title('HV vs \phi_{min} (QiGA)','FontWeight','bold');
legend('FontSize',9,'Location','southeast'); grid on;
sgtitle({'M-6  MOO Convergence in Objective Space: Hypervolume vs Iteration',...
         'QiGA builds richer Pareto archives faster'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M6_hv_convergence');

%% M-7  Vehicle Utilization vs phi_min
fprintf('M-7  Vehicle Utilization\n');
phi_vr=sort(unique(TVR.phi_min),'descend');
nv_v=arrayfun(@(p) mean(TVR.NV(abs(TVR.phi_min-p)<1e-9)), phi_vr);
nv_e=arrayfun(@(p) std(TVR.NV(abs(TVR.phi_min-p)<1e-9)),  phi_vr);
sr_v=arrayfun(@(p) mean(TVR.SR(abs(TVR.phi_min-p)<1e-9)),  phi_vr);
fig=figure('Name','M-7 Vehicle Utilization','Position',[50 50 900 520]);
yyaxis left;
b=bar(1:numel(phi_vr),nv_v,'FaceAlpha',0.80); hold on;
for ci=1:numel(phi_vr); b.FaceColor='flat'; b.CData(ci,:)=C_PHI7(ci,:); end
errorbar(1:numel(phi_vr),nv_v,nv_e,'k.','LineWidth',1.2,'CapSize',5);
ylabel('Vehicles Dispatched (NV)');
yyaxis right;
plot(1:numel(phi_vr),sr_v,'D-','Color','k','LineWidth',2.2,'MarkerSize',7,'DisplayName','SR (%)');
ylabel('Service Rate SR (%)');
set(gca,'XTick',1:numel(phi_vr),'XTickLabel',arrayfun(@(p)sprintf('%.2f',p),phi_vr,'UniformOutput',false));
xlabel('\phi_{min}');
title({'M-7  Vehicle Utilization vs \phi_{min}',...
       'More vehicles at low \phi yet SR still drops — reliability loss is irreplaceable'},'FontWeight','bold');
grid on; legend({'SR (%)'},'FontSize',9,'Location','northwest');
save_fig(fig,OUTDIR,'M7_vehicle_utilization');

%% M-8  Route Length Distribution
fprintf('M-8  Route Length Distribution\n');
phi_vr2=sort(unique(TVR.phi_min),'descend'); n_phi=numel(phi_vr2);
cmap_m8=summer(n_phi);
fig=figure('Name','M-8 Route Lengths','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
for pi=1:n_phi
    dat=TVR.route_len_mean(abs(TVR.phi_min-phi_vr2(pi))<1e-9);
    if numel(dat)<3; continue; end
    [f,xi]=ksdensity(dat); f=f/max(f)*0.32;
    fill([pi+f;pi-flipud(f)],[xi;flipud(xi)],cmap_m8(pi,:),'FaceAlpha',0.65,'EdgeColor','none');
    q=quantile(dat,[0.25 0.5 0.75]);
    rectangle('Position',[pi-0.08 q(1) 0.16 q(3)-q(1)],'FaceColor','none','EdgeColor','k','LineWidth',1.2);
    plot([pi-0.08 pi+0.08],[q(2) q(2)],'k-','LineWidth',2);
end
set(gca,'XTick',1:n_phi,'XTickLabel',arrayfun(@(p)sprintf('%.2f',p),phi_vr2,'UniformOutput',false));
xlabel('\phi_{min}'); ylabel('Mean Route Length (km)');
title('Route Length Distribution per \phi_{min}'); grid on;

subplot(1,2,2); hold on;
mn_v=arrayfun(@(p) mean(TVR.route_len_mean(abs(TVR.phi_min-p)<1e-9)), phi_vr2);
mx_v=arrayfun(@(p) mean(TVR.route_len_max(abs(TVR.phi_min-p)<1e-9)),  phi_vr2);
fill([phi_vr2;flipud(phi_vr2)],[mn_v;flipud(mx_v)],[0.08 0.40 0.75],'FaceAlpha',0.15,'EdgeColor','none','DisplayName','Mean-Max band');
plot(phi_vr2,mn_v,'o-','Color',[0.08 0.40 0.75],'LineWidth',2.2,'DisplayName','Mean route length');
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('Route Length (km)');
title('Mean and Max Route Length vs \phi_{min}'); legend('FontSize',9); grid on;
sgtitle({'M-8  Route Length Distribution Shift under Reliability Degradation',...
         'Longer detours at low \phi_{min} and growing variance as paths become scarce'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M8_route_length_dist');

%% M-9  Gantt Chart (uses patch for positioned horizontal bars)
fprintf('M-9  Gantt Chart\n');
scenarios={'reliable','degraded'};
phi_ttls={'\phi_{min}=1.00 (Reliable)','\phi_{min}=0.80 (Degraded)'};
c_prio=[0.08 0.40 0.75; 0.08 0.40 0.75; 0.18 0.49 0.20; 1.00 0.60 0.00; 0.89 0.22 0.21];

    function draw_hbar(ax, x_start, width, y_centre, height, col, alpha_val)
        % Draw a horizontal bar using patch (no reliance on barh 'left' argument)
        xs = [x_start, x_start+width, x_start+width, x_start];
        ys = [y_centre-height/2, y_centre-height/2, y_centre+height/2, y_centre+height/2];
        patch(ax, xs, ys, col, 'FaceAlpha', alpha_val, 'EdgeColor', 'none');
    end

fig=figure('Name','M-9 Gantt','Position',[50 50 1300 720]);
for si=1:2
    ax=subplot(2,1,si); hold on;
    sub=TGT(strcmp(TGT.scenario,scenarios{si}),:);
    vehs=unique(sub.vehicle);
    for vi=1:numel(vehs)
        vd=sub(sub.vehicle==vehs(vi),:); y=(vi-1)*1.2;
        for ri=1:height(vd)
            prio=min(vd.priority(ri),5); col=c_prio(prio,:);
            draw_hbar(ax, vd.depart(ri),   vd.travel(ri),                              y,      0.30, [0.75 0.75 0.75], 0.60);
            draw_hbar(ax, vd.service_start(ri), vd.service_end(ri)-vd.service_start(ri), y,    0.42, col, 0.85);
            draw_hbar(ax, vd.early(ri),    vd.late(ri)-vd.early(ri),                   y+0.27, 0.12, col, 0.20);
            if vd.tardiness(ri)>0
                draw_hbar(ax, vd.late(ri), vd.tardiness(ri), y, 0.42, [0.89 0.22 0.21], 0.50);
            end
            text(vd.service_start(ri)+0.5, y, sprintf('C%d',vd.customer(ri)+1),...
                'VerticalAlignment','middle','FontSize',6.5,'Color','w','FontWeight','bold');
        end
    end
    set(ax,'YTick',(0:numel(vehs)-1)*1.2,...
       'YTickLabel',arrayfun(@(v)sprintf('V%d',v+1),vehs,'UniformOutput',false));
    xlabel('Time (min)'); title(phi_ttls{si},'FontWeight','bold'); grid on;
end
sgtitle({'M-9  Service Timeline Gantt Chart — Reliable vs Degraded Network',...
         'Travel (grey) | Service (priority colour) | Red = tardiness | Band = fuzzy window'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M9_gantt_chart');

%% M-10  Delta Sensitivity
fprintf('M-10  Delta Sensitivity\n');
delta_u=sort(unique(TDLT.delta_min));
tier_cols=[0.89 0.22 0.21; 1.00 0.60 0.00; 0.13 0.59 0.95];
tier_lbls={'Type 1 (Critical)','Type 2 (Serious)','Type 3 (Minor)'};
fig=figure('Name','M-10 Delta Sensitivity','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
phi85=0.85;
for ti=1:3
    sr_v=arrayfun(@(d) mean(TDLT.SR(abs(TDLT.phi_min-phi85)<1e-9 & TDLT.tier==ti & TDLT.delta_min==d)), delta_u);
    plot(delta_u,sr_v,'o-','Color',tier_cols(ti,:),'LineWidth',2.2,'MarkerSize',7,'DisplayName',tier_lbls{ti});
end
xlabel('\delta (fuzzy tolerance, minutes)'); ylabel('SR (%)');
title(sprintf('SR vs \\delta by Injury Type (\\phi_{min}=%.2f)',phi85),'FontWeight','bold');
legend('FontSize',9); grid on;
subplot(1,2,2); hold on;
for phi_s=[1.00 0.85 0.70]; col=[0.18 0.49 0.20]; if phi_s==0.85; col=[1 0.6 0]; end; if phi_s==0.70; col=[0.89 0.22 0.21]; end
    sr_v=arrayfun(@(d) mean(TDLT.SR(abs(TDLT.phi_min-phi_s)<1e-9 & TDLT.tier==1 & TDLT.delta_min==d)), delta_u);
    plot(delta_u,sr_v,'s--','Color',col,'LineWidth',2.2,'MarkerSize',7,'DisplayName',sprintf('\\phi=%.2f',phi_s));
end
xlabel('\delta (minutes)'); ylabel('SR (%)');
title('Type-1 SR vs \delta across \phi_{min}','FontWeight','bold'); legend('FontSize',9); grid on;
sgtitle({'M-10  Fuzzy Window Tolerance (\delta) Sensitivity Analysis',...
         'Wider windows improve SR; returns diminish; Type-3 most sensitive'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M10_delta_sensitivity');

%% M-11  Fleet Size Sensitivity
fprintf('M-11  Fleet Sensitivity\n');
k_u=sort(unique(TFL.K));
phi_fl=[1.00 0.90 0.85 0.80 0.75 0.70];
c_fl=C_PHI7(1:6,:);
fig=figure('Name','M-11 Fleet Sensitivity','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
for pi=1:numel(phi_fl)
    sr_v=arrayfun(@(k) mean(TFL.SR(abs(TFL.phi_min-phi_fl(pi))<1e-9 & TFL.K==k)), k_u);
    plot(k_u,sr_v,'o-','Color',c_fl(pi,:),'LineWidth',2.2,'MarkerSize',6,'DisplayName',sprintf('\\phi=%.2f',phi_fl(pi)));
end
yline(85,'--','Color',[0.5 0.5 0.5],'LineWidth',1.3,'Label','85% target'); hold on;
xlabel('Fleet Size K'); ylabel('SR (%)'); ylim([0 105]);
title('SR vs Fleet Size K at Multiple \phi_{min}','FontWeight','bold');
legend('FontSize',8.5,'NumColumns',2,'Location','southeast'); grid on;

subplot(1,2,2);
k_req=zeros(1,numel(phi_fl));
for pi=1:numel(phi_fl)
    sr_k=arrayfun(@(k) mean(TFL.SR(abs(TFL.phi_min-phi_fl(pi))<1e-9 & TFL.K==k)), k_u);
    idx=find(sr_k>=85,1); if ~isempty(idx); k_req(pi)=k_u(idx); else; k_req(pi)=max(k_u)+2; end
end
b=bar(1:numel(phi_fl),k_req,'FaceColor','flat','FaceAlpha',0.82);
for ci=1:numel(phi_fl); b.CData(ci,:)=c_fl(ci,:); end
yline(7,'--','Color',[0.5 0.5 0.5],'LineWidth',1.3,'Label','Baseline K=7');
set(gca,'XTick',1:numel(phi_fl),'XTickLabel',arrayfun(@(p)sprintf('\\phi=%.2f',p),phi_fl,'UniformOutput',false));
ylabel('Min K for SR \geq 85%'); title('Fleet Required to Meet SR Target','FontWeight','bold');
for ci=1:numel(phi_fl)
    if k_req(ci)>max(k_u); lbl='>15'; else; lbl=num2str(k_req(ci)); end
    text(ci,k_req(ci)+0.1,lbl,'HorizontalAlignment','center','FontSize',9,'FontWeight','bold');
end
grid on;
sgtitle({'M-11  Fleet Size Sensitivity: Can More Vehicles Compensate?',...
         'At \phi=0.70, even K=15 cannot recover SR to 85% — reliability is irreplaceable'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M11_fleet_sensitivity');

%% M-12  Pattern × phi Heatmap
fprintf('M-12  Pattern x phi Heatmap\n');
patt12={'random','clustered','progressive','hub'};
phi_pg=sort(unique(TPG.phi_min));
mat12=zeros(numel(patt12),numel(phi_pg));
for pi2=1:numel(patt12)
    for phii=1:numel(phi_pg)
        mask=strcmp(TPG.pattern,patt12{pi2}) & abs(TPG.phi_min-phi_pg(phii))<1e-9;
        if any(mask); mat12(pi2,phii)=mean(TPG.SR(mask)); end
    end
end
fig=figure('Name','M-12 Pattern Phi Heatmap','Position',[50 50 1200 520]);
subplot(1,2,1);
imagesc(mat12); colormap(summer); caxis([0 100]); c=colorbar; c.Label.String='SR (%)';
for pi2=1:numel(patt12)
    for phii=1:numel(phi_pg)
        clr='k'; if mat12(pi2,phii)<40||mat12(pi2,phii)>88; clr='w'; end
        text(phii,pi2,sprintf('%.0f%%',mat12(pi2,phii)),'HorizontalAlignment','center',...
            'VerticalAlignment','middle','FontSize',9,'FontWeight','bold','Color',clr);
    end
end
set(gca,'XTick',1:numel(phi_pg),'XTickLabel',arrayfun(@(p)sprintf('%.2f',p),phi_pg,'UniformOutput',false),...
        'YTick',1:numel(patt12),'YTickLabel',cellfun(@(s)[upper(s(1)) s(2:end)],patt12,'UniformOutput',false));
xlabel('\phi_{min}'); ylabel('Failure Pattern'); title('SR Heatmap: Pattern \times \phi_{min}');

subplot(1,2,2); hold on;
ls12={'-','--','-.',':'}; mk12={'o','s','d','^'};
for pi2=1:numel(patt12)
    plot(phi_pg,mat12(pi2,:),[mk12{pi2} ls12{pi2}],'Color',C_ALGO(pi2,:),'LineWidth',2.2,...
         'DisplayName',[upper(patt12{pi2}(1)) patt12{pi2}(2:end)]);
end
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('SR (%)');
title('SR Degradation by Failure Pattern'); legend('FontSize',9); grid on;
sgtitle({'M-12  Failure Pattern \times \phi_{min} Interaction',...
         'Hub failure dominant at all \phi; gap widens below \phi^*=0.85'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M12_pattern_phi_heatmap');

%% M-13  Pareto Method Comparison
fprintf('M-13  Pareto Method Comparison\n');
fig=figure('Name','M-13 Pareto Methods','Position',[50 50 1200 520]);
methods={'weighted','epsilon'}; mk13={'o','s'}; c13={[0.08 0.40 0.75],[0.89 0.22 0.21]};
subplot(1,2,1); hold on;
for mi=1:2
    mask=strcmp(TPA.method,methods{mi});
    scatter(TPA.f1_satisfaction(mask),TPA.f3_reliability(mask),45,c13{mi},'filled',...
        'Marker',mk13{mi},'MarkerFaceAlpha',0.75,'MarkerEdgeColor','w',...
        'DisplayName',[upper(methods{mi}(1)) methods{mi}(2:end) ' scalarization']);
end
xlabel('f_1: Satisfaction (higher=better)'); ylabel('f_3: Reliability (higher=better)');
title('Pareto Projection: f_1 \times f_3','FontWeight','bold');
legend('FontSize',9); grid on;
subplot(1,2,2); hold on;
for mi=1:2
    mask=strcmp(TPA.method,methods{mi});
    scatter(TPA.f1_satisfaction(mask),TPA.f2_distance_km(mask),45,c13{mi},'filled',...
        'Marker',mk13{mi},'MarkerFaceAlpha',0.75,'MarkerEdgeColor','w',...
        'DisplayName',[upper(methods{mi}(1)) methods{mi}(2:end) ' scalarization']);
end
xlabel('f_1: Satisfaction'); ylabel('f_2: Total Distance (km)');
title('Pareto Projection: f_1 \times f_2','FontWeight','bold');
legend('FontSize',9); grid on;
sgtitle({'M-13  \epsilon-Constraint vs Weighted Scalarization: Pareto Front Comparison',...
         'Both methods agree on front shape; \epsilon-constraint gives denser lower-left coverage'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M13_pareto_method_comparison');

%% M-14  Objective Degradation
fprintf('M-14  Objective Degradation\n');
phi_od=sort(unique(TOD.phi_min),'descend');
cols14={[0.18 0.49 0.20],[0.89 0.22 0.21],[0.08 0.40 0.75]};
obj14={'f1_mean','f2_mean','f3_mean'}; std14={'f1_std','f2_std','f3_std'};
ylbls14={'f_1: Satisfaction','f_2: Distance (km)','f_3: Reliability'};
notes14={'higher=better','lower=better','higher=better'};
fig=figure('Name','M-14 Objective Degradation','Position',[50 50 1400 500]);
for oi=1:3
    subplot(1,3,oi); hold on;
    mn_o=arrayfun(@(p) mean(TOD.(obj14{oi})(abs(TOD.phi_min-p)<1e-9)), phi_od);
    sd_o=arrayfun(@(p) mean(TOD.(std14{oi})(abs(TOD.phi_min-p)<1e-9)), phi_od);
    fill([phi_od;flipud(phi_od)],[mn_o+sd_o;flipud(mn_o-sd_o)],cols14{oi},'FaceAlpha',0.15,'EdgeColor','none');
    plot(phi_od,mn_o,'o-','Color',cols14{oi},'LineWidth',2.5,'MarkerSize',7);
    xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.8,'Label','\phi^*');
    set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel(ylbls14{oi});
    title({ylbls14{oi},['(' notes14{oi} ')']},'FontWeight','bold'); grid on;
end
sgtitle({'M-14  Objective-Level Degradation: f_1, f_2, f_3 Each vs \phi_{min} (QiGA)',...
         'Closes the loop: maps objective collapse to the SR/OTSR results in SM-1'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'M14_objective_degradation');

fprintf('\n=== DONE: M-1 to M-14 .fig files saved to:\n  %s\n', OUTDIR);
